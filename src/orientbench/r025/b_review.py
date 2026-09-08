"""Independent native-label replay. Reads the server without writing any files."""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from shapely.geometry import Polygon
from shapely.strtree import STRtree


def native(path):
    rows, groups, invalid = {}, defaultdict(list), {}
    for number, text in enumerate(path.read_text().splitlines(), 1):
        if not text.strip() or text.lower().startswith(("imagesource:", "gsd:", "acquisition date:")):
            continue
        values = text.split()
        if len(values) != 10:
            invalid[number] = "missing_difficult" if len(values) == 9 else "invalid_field_count"
            continue
        try:
            points = tuple(zip(map(float, values[:8:2]), map(float, values[1:8:2])))
            poly = Polygon(points)
            if not poly.is_valid or poly.area <= 0 or values[9] not in {"0", "1", "2"}:
                invalid[number] = "invalid_native_record"
                continue
            variants = []
            for sequence in (points, points[::-1]):
                for offset in range(4):
                    variants.append(sequence[offset:]+sequence[:offset])
            # Current native inputs are checked below for exact 1e-6 grid membership.
            if any(abs(c*1e6-round(c*1e6)) > 1e-5 for p in points for c in p):
                raise ValueError("off-grid coordinate needs explicit tolerance review")
            key = min(variants)
            rows[number] = (key, values[8], values[9], poly)
            groups[key].append(number)
        except (ValueError, OverflowError):
            invalid[number] = "unparseable_native_record"
    return rows, groups, invalid


def replay(old_path, new_path):
    left, lg, li = native(old_path)
    right, rg, ri = native(new_path)
    results, blocked_l, blocked_r = {}, set(), set()
    for key in lg.keys() | rg.keys():
        a, b = lg.get(key, []), rg.get(key, [])
        if len(a) > 1 or len(b) > 1:
            blocked_l.update(a); blocked_r.update(b)
            for n in a: results[(n, 0)] = ("exact_duplicate_ambiguous", None)
            for n in b: results[(0, n)] = ("exact_duplicate_ambiguous", None)
        elif a and b:
            blocked_l.add(a[0]); blocked_r.add(b[0])
            status = "geometry_unchanged" if left[a[0]][1:3] == right[b[0]][1:3] else "class_or_difficult_only"
            results[(a[0], b[0])] = (status, 1.)
    ids = sorted(set(right)-blocked_r)
    tree = STRtree([right[n][3] for n in ids])
    links = {}
    degrees_l, degrees_r = Counter(), Counter()
    for a in sorted(set(left)-blocked_l):
        for index in tree.query(left[a][3]):
            b = ids[int(index)]
            intersect = left[a][3].intersection(right[b][3]).area
            overlap = intersect/(left[a][3].area+right[b][3].area-intersect)
            if overlap >= .5:
                links[(a, b)] = overlap
                degrees_l[a] += 1; degrees_r[b] += 1
    paired_l, paired_r = set(), set()
    for (a, b), overlap in links.items():
        if degrees_l[a] == degrees_r[b] == 1:
            status = "geometry_revised" if left[a][1:3] == right[b][1:3] else "geometry_revised_and_metadata_changed"
            results[(a, b)] = (status, overlap)
            paired_l.add(a); paired_r.add(b)
    for a in left.keys()-blocked_l-paired_l:
        results[(a, 0)] = ("old_iou_ambiguous" if degrees_l[a] else "old_no_candidate", None)
    for b in right.keys()-blocked_r-paired_r:
        results[(0, b)] = ("new_iou_ambiguous" if degrees_r[b] else "new_no_candidate", None)
    return left, right, li, ri, results, links


def review(root, run_id, output_dir=None):
    out = Path(output_dir).resolve() if output_dir else root / f"runs/{run_id}/artifacts"
    cfg = json.loads((root / f"configs/{run_id}/protocol.json").read_text())
    data = Path(cfg["dataset_root"])
    old = {p.stem:p for p in (data/cfg["v1_labels"]).glob('*.txt')}
    new = {p.stem:p for p in (data/cfg["v2_labels"]).glob('*.txt')}
    with (out/'image_pairs.csv').open(newline='') as f: images = list(csv.DictReader(f))
    with (out/'label_correspondence.csv').open(newline='') as f: observed = list(csv.DictReader(f))
    actual = defaultdict(list)
    for r in observed: actual[r['image_id']].append(r)
    summary, focus, invalid = Counter(), Counter(), []
    mismatches, native_hashes, totals, example = [], [], Counter(), []
    expected_links = {}
    expected_edges = 0
    for image in images:
        name = image['image_id']
        if image['status'] not in {'byte_identical', 'pixel_identical_encoding_diff'}: continue
        if name not in old or name not in new:
            mismatches.append([name,'missing_native_label']); continue
        for path in [old[name],new[name]]:
            native_hashes.append([str(path),hashlib.sha256(path.read_bytes()).hexdigest()])
        a,b,ia,ib,wanted,edges = replay(old[name],new[name])
        invalid.extend([[name,'old',n,e] for n,e in ia.items()])
        invalid.extend([[name,'new',n,e] for n,e in ib.items()])
        totals['old_objects']+=len(a)+len(ia); totals['new_objects']+=len(b)+len(ib)
        expected_edges += len(edges)
        expected_links.update({(name,i,j):v for (i,j),v in edges.items()})
        for (i,j),(status,iou) in wanted.items():
            summary[status]+=1
            if (i and a[i][1] in {'plane','ship'}) or (j and b[j][1] in {'plane','ship'}):
                focus[status]+=1
                if status.startswith('geometry_revised') and len(example)<3:
                    example.append({'image':name,'old_line':i,'new_line':j,'iou':iou})
        got = {(int(r['old_line'] or 0),int(r['new_line'] or 0)):r for r in actual[name]}
        if len(got)!=len(actual[name]): mismatches.append([name,'duplicate_output_row'])
        if set(got)!=set(wanted): mismatches.append([name,'correspondence_keys'])
        for key in set(got)&set(wanted):
            status,iou=wanted[key]; r=got[key]
            if r['status'] != status or (iou is not None and abs(float(r['iou'])-iou)>1e-9):
                mismatches.append([name,'status_or_iou',*key])
            i,j=key
            for side,number,records in [('old',i,a),('new',j,b)]:
                if number and (r[side+'_class'],r[side+'_difficult']) != records[number][1:3]:
                    mismatches.append([name,'metadata',*key])
            if i and j:
                shift=a[i][3].centroid.distance(b[j][3].centroid)
                ratio=b[j][3].area/a[i][3].area
                if abs(float(r['centroid_shift'])-shift)>1e-8 or abs(float(r['area_ratio'])-ratio)>1e-9:
                    mismatches.append([name,'geometry_measurement',*key])
    with (out/'candidate_edges.csv').open(newline='') as f:
        observed_edges=list(csv.DictReader(f))
    got_links={(r['image_id'],int(r['old_line']),int(r['new_line'])):float(r['iou']) for r in observed_edges}
    edge_mismatches=len(set(got_links)^set(expected_links))
    edge_mismatches+=sum(abs(got_links[k]-expected_links[k])>1e-9 for k in set(got_links)&set(expected_links))
    if len(got_links)!=len(observed_edges): edge_mismatches+=1
    # Fail closed on malformed native inputs rather than inheriting the producer's omissions.
    return {'utc':datetime.now(timezone.utc).isoformat(),'run_id':run_id,
            'native_label_files':len(native_hashes),'native_hashes':native_hashes,
            'totals':dict(totals),'corrected_status':dict(summary),'corrected_focus_status':dict(focus),
            'candidate_edges':expected_edges,'invalid_native_records':invalid,
            'disagreement_count':len(mismatches),'disagreement_examples':mismatches[:10],
            'candidate_edge_mismatches':edge_mismatches,
            'geometry_examples':example,'pass':not mismatches and not invalid and not edge_mismatches,
            'scope':'Native label correspondence replay; not an independent image decode or prediction-source audit.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--run-id',choices=['r025','r026','r027'],default='r025')
    parser.add_argument('--output-dir', type=Path)
    args=parser.parse_args()
    print(json.dumps(review(args.root,args.run_id,args.output_dir),ensure_ascii=False,indent=2))
