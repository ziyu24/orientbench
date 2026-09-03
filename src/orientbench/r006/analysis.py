"""Frozen r006 RP1/cluster-bootstrap gate calculation (primary implementation)."""
from __future__ import annotations

import argparse
import json
import math
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

from orientbench.r005.matcher import global_match


def _array(value): return np.asarray(value.detach().cpu(), dtype=float)
def _read(path):
    with Path(path).open("rb") as handle: return pickle.load(handle)
def _theta(box): return (float(box[4]) + (math.pi / 2 if float(box[3]) > float(box[2]) else 0.0)) % math.pi
def _dpi(a, b): return min(abs((a-b) % math.pi), abs((b-a) % math.pi)) * 2.0 / math.pi


def _by_id(condition): return {str(row["img_id"]): row for row in condition["records"]}
def _matched(gt, record):
    boxes = np.asarray(record["bboxes"], float)
    return {g: p for g, p in global_match(gt, boxes)}


def _holm(rows):
    order = sorted(range(len(rows)), key=lambda i: rows[i]["p"])
    ceiling = 0.0
    for rank, index in enumerate(order):
        ceiling = max(ceiling, (len(rows)-rank)*rows[index]["p"])
        rows[index]["holm_p"] = min(1., ceiling)
        rows[index]["passed"] = bool(rows[index]["theta"] > 0 and rows[index]["holm_p"] <= .05)


def _boot(values, global_draws, global_images):
    # values is image_id -> complete-denominator image mean.
    images = sorted(values); x = np.asarray([values[i] for i in images], float)
    local = {image: index for index, image in enumerate(images)}
    lookup = np.asarray([local.get(image, -1) for image in global_images], dtype=np.int32)
    picked = lookup[global_draws]; valid = picked >= 0
    # One frozen official-image draw is used by every unit.  Objects outside a
    # unit's pre-frozen registry are excluded from both numerator and
    # denominator, never converted to zero-valued observations.
    sampled = (x[np.maximum(picked, 0)] * valid).sum(1) / valid.sum(1)
    point = float(x.mean())
    p = (1 + int(np.count_nonzero((sampled-point) >= point))) / (len(global_draws)+1)
    return point, p, np.quantile(sampled, [.025, .975]).tolist()


def _phase0(sweep):
    for condition in sweep["conditions"]:
        if condition["axis"] == "x" and condition["shift"] == 0 and condition["repeat"] == 0:
            return _by_id(condition)
    raise RuntimeError("missing registered phase zero")


def _condition(sweep, axis, shift):
    for item in sweep["conditions"]:
        if item["axis"] == axis and item["shift"] == shift and item["repeat"] == 0:
            return _by_id(item)
    raise RuntimeError(f"missing {axis}/{shift}")


def _determinism(gt_map, sweep):
    base = _phase0(sweep); repeats = [_by_id(c) for c in sweep["conditions"] if c["axis"] == "x" and c["shift"] == 0]
    if len(repeats) != 3: raise RuntimeError("r006 requires exactly three phase-zero repeats")
    keys_ok, maximum = True, 0.0
    for image_id, gt in gt_map.items():
        reference = _matched(gt, base[image_id])
        for repeat in repeats[1:]:
            other = _matched(gt, repeat[image_id])
            keys_ok &= reference.keys() == other.keys()
            for g in reference.keys() & other.keys():
                a = np.asarray(base[image_id]["bboxes"], float)[reference[g]]
                b = np.asarray(repeat[image_id]["bboxes"], float)[other[g]]
                maximum = max(maximum, _dpi(_theta(a), _theta(b)))
    return {"keys_identical": keys_ok, "max_canonical_angle_difference_deg": maximum,
            "passed": bool(keys_ok and maximum <= .05)}


def _unit(gt_map, sweep, stride, axis):
    base = _phase0(sweep); max_shift = 2*stride
    shifts = [_condition(sweep, axis, d) for d in range(max_shift)]
    universe = []
    retained = [0]*max_shift
    images_by_shift = [set() for _ in range(max_shift)]
    for image_id, gt in gt_map.items():
        base_pair = _matched(gt, base[image_id])
        for g, p in base_pair.items():
            if int(base[image_id]["source_stride"][p]) == stride:
                universe.append((image_id, g, p))
    for image_id, g, _ in universe:
        for d, rows in enumerate(shifts):
            pairs = _matched(gt_map[image_id], rows[image_id])
            p = pairs.get(g)
            if p is not None and int(rows[image_id]["source_stride"][p]) == stride:
                retained[d] += 1; images_by_shift[d].add(image_id)
    per_image = defaultdict(lambda: {"A": [], "R": [], "stableA": [], "stableR": []})
    stable_count, stable_images = 0, set()
    for image_id, g, p0 in universe:
        series, valid = [], []
        clean = np.asarray(base[image_id]["bboxes"], float)[p0]
        clean_score = float(base[image_id]["scores"][p0]); scale = max(float(clean[2]), float(clean[3]), 1e-12)
        for rows in shifts:
            pairs = _matched(gt_map[image_id], rows[image_id]); p = pairs.get(g)
            if p is None or int(rows[image_id]["source_stride"][p]) != stride:
                series.append(None); valid.append(False); continue
            box = np.asarray(rows[image_id]["bboxes"], float)[p]
            series.append((box, float(rows[image_id]["scores"][p])))
            valid.append(True)
        terms_a, terms_r = [], []
        for c in (0, 1):
            for q in range(1, stride):
                left, right = c*stride+q, c*stride
                terms_a.append(_dpi(_theta(series[left][0]), _theta(series[right][0])) if valid[left] and valid[right] else 0.)
        for q in range(stride):
            terms_r.append(_dpi(_theta(series[q+stride][0]), _theta(series[q][0])) if valid[q+stride] and valid[q] else 0.)
        a, r = float(np.mean(terms_a)), float(np.mean(terms_r))
        stable = all(valid)
        if stable:
            for box, score in (entry for entry in series if entry is not None):
                center = math.hypot(float(box[0]-clean[0]), float(box[1]-clean[1])) / scale
                side = sorted((float(box[2]),float(box[3]))); clean_side = sorted((float(clean[2]),float(clean[3])))
                stable &= center <= .02 and max(abs(math.log(side[0]/clean_side[0])), abs(math.log(side[1]/clean_side[1]))) <= .02 and abs(score-clean_score) <= .05
        if stable: stable_count += 1; stable_images.add(image_id)
        per_image[image_id]["A"].append(a); per_image[image_id]["R"].append(r)
        per_image[image_id]["stableA"].append(a if stable else 0.); per_image[image_id]["stableR"].append(r if stable else 0.)
    metrics = {key: {image: float(np.mean(values[key])) for image, values in per_image.items()} for key in ("A","R","stableA","stableR")}
    retention = [{"shift": d, "retained": retained[d], "retention": retained[d]/len(universe) if universe else 0., "images": len(images_by_shift[d]),
                  "passed": bool(retained[d] >= .9*len(universe) and retained[d] >= 100 and len(images_by_shift[d]) >= 50)} for d in range(max_shift)]
    return {"objects":len(universe), "images":len(per_image), "retention":retention, "stable_objects":stable_count,
            "stable_images":len(stable_images), "stable_coverage":stable_count/len(universe) if universe else 0., "metrics":metrics,
            "valid": all(row["passed"] for row in retention)}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--r004-root",type=Path,required=True); parser.add_argument("--census",type=Path,required=True); parser.add_argument("--orcnn",type=Path,required=True); parser.add_argument("--rtmdet",type=Path,required=True); parser.add_argument("--out",type=Path,required=True); parser.add_argument("--draws",type=Path,required=True); args=parser.parse_args()
    census=json.loads(args.census.read_text()); sweeps={"oriented_rcnn_r50":_read(args.orcnn),"rotated_rtmdet_m":_read(args.rtmdet)}
    gt_paths={name:args.r004_root/f"inference/test/{name}/clean/predictions.pkl" for name in sweeps}; gt_maps={name:{str(r["img_id"]):_array(r["gt_instances"]["bboxes"]) for r in _read(path)} for name,path in gt_paths.items()}
    global_images=sorted(set().union(*(set(rows) for rows in gt_maps.values()))); rng=np.random.default_rng(6006); global_draws=rng.integers(0,len(global_images),size=(10000,len(global_images)),dtype=np.int16)
    units={}; main_rows=[]; stable_rows=[]; draw_store={"global_image_ids":np.asarray(global_images),"global_draws":global_draws}
    for name,sweep in sweeps.items():
        gt_map=gt_maps[name]; det=_determinism(gt_map,sweep); eligible=census[name]["eligible_strides"]
        units[name]={"determinism":det,"eligible":eligible,"axes":{}}
        for stride in eligible:
            for axis in ("x","y"):
                unit=_unit(gt_map,sweep,stride,axis); units[name]["axes"][f"{stride}/{axis}"]=unit
                for label, values in (("A-0.01",{i:v-.01 for i,v in unit["metrics"]["A"].items()}),("A-R-0.005",{i:unit["metrics"]["A"][i]-unit["metrics"]["R"][i]-.005 for i in unit["metrics"]["A"]}),("A-2R",{i:unit["metrics"]["A"][i]-2*unit["metrics"]["R"][i] for i in unit["metrics"]["A"].items()})):
                    theta,p,ci=_boot(values,global_draws,global_images); main_rows.append({"model":name,"stride":stride,"axis":axis,"gate":label,"theta":theta,"p":p,"ci95":ci})
                vals={i:unit["metrics"]["stableA"][i]-unit["metrics"]["stableR"][i]-.0025 for i in unit["metrics"]["stableA"]}; theta,p,ci=_boot(vals,global_draws,global_images); stable_rows.append({"model":name,"stride":stride,"axis":axis,"gate":"Astable-Rstable-0.0025","theta":theta,"p":p,"ci95":ci})
    _holm(main_rows); _holm(stable_rows)
    for name in sweeps:
        family=False
        for stride in units[name]["eligible"]:
            axes=[axis for axis in ("x","y") if units[name]["axes"][f"{stride}/{axis}"]["valid"] and units[name]["axes"][f"{stride}/{axis}"]["stable_coverage"] >= .5 and units[name]["axes"][f"{stride}/{axis}"]["stable_objects"] >= 100 and units[name]["axes"][f"{stride}/{axis}"]["stable_images"] >= 50]
            passed=lambda axis: all(r["passed"] for r in main_rows if r["model"]==name and r["stride"]==stride and r["axis"]==axis) and all(r["passed"] for r in stable_rows if r["model"]==name and r["stride"]==stride and r["axis"]==axis)
            family |= len(axes)==2 and all(passed(axis) for axis in axes)
        units[name]["family_witness"]=family
    validity=all(units[n]["determinism"]["passed"] and all(u["valid"] for u in units[n]["axes"].values()) for n in units)
    token="INCONCLUSIVE_R006_EXECUTION_VALIDITY" if not validity else ("ADMIT_BIAXIAL_TAL_METHOD_STAGE" if all(units[n]["family_witness"] for n in units) else "KILL_CROSS_FAMILY_BIAXIAL_TAL_R006")
    args.draws.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(args.draws,**draw_store); args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps({"protocol":"r006-primary-analysis-v1","units":units,"main_holm":main_rows,"stable_holm":stable_rows,"validity":validity,"token":token,"draws":str(args.draws)},indent=2)+"\n")

if __name__=="__main__": main()
