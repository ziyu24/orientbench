"""CPU finite-population simulation of fixed predictions; no training."""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import pickle
import platform
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
import torch
from mmrotate.datasets.hrsc import HRSCDataset
from mmrotate.structures.bbox import qbox2rbox
from mmrotate.evaluation.functional.mean_ap import tpfp_default, eval_rbbox_map

from orientbench.r028.run import trace_image
from orientbench.r029.sampling import estimate, sample_plans, strata


def check(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def arr(x):
    return x.detach().cpu().numpy() if hasattr(x, 'detach') else np.asarray(x)


def read_native(dataset, cfg):
    """Validate the native population before either inference or evaluation."""
    frozen = cfg['input_sha256']
    for name in ['test.txt', 'trainval.txt']:
        check(digest(dataset / 'splits' / name) == frozen[name], f'changed split {name}')
    ids = (dataset / 'splits/test.txt').read_text().split()
    train = (dataset / 'splits/trainval.txt').read_text().split()
    check(len(ids) == len(set(ids)) == cfg['population_size'], 'test ID count/duplicates')
    check(len(train) == len(set(train)) == cfg['trainval_size'], 'trainval ID count/duplicates')
    check(not set(ids) & set(train), 'trainval/test overlap')
    manifest = [(i, digest(dataset / 'annfiles' / f'{i}.xml')) for i in ids]
    xml_hash = hashlib.sha256(json.dumps(manifest, separators=(',', ':')).encode()).hexdigest()
    check(xml_hash == frozen['xml_manifest'], 'changed native XML population')
    native = HRSCDataset(ann_file=str(dataset / 'splits/test.txt'),
                        data_prefix={'sub_data_root': str(dataset)}, img_subdir='images',
                        ann_subdir='annfiles', pipeline=[], test_mode=True)
    loaded = [native.get_data_info(i) for i in range(len(native))]
    check([x['img_id'] for x in loaded] == ids, 'loader coverage/order mismatch')
    annotations, shapes, xml_difficult = [], {}, 0
    for image_id, info in zip(ids, loaded):
        xml = ET.parse(dataset / 'annfiles' / f'{image_id}.xml').getroot()
        objs = xml.findall('./HRSC_Objects/HRSC_Object')
        xml_difficult += sum(int(o.findtext('difficult', '0')) != 0 for o in objs)
        check(len(info['instances']) == len(objs), 'native objects dropped')
        pixels = cv2.imread(str(dataset / 'images' / f'{image_id}.bmp'))
        check(pixels is not None, f'missing/unreadable image {image_id}')
        shapes[image_id] = pixels.shape[:2]
        check(pixels.shape[:2] == (int(xml.findtext('Img_SizeHeight')),
                                   int(xml.findtext('Img_SizeWidth'))), 'XML/image shape mismatch')
        regular, ignored = [], []
        for x in info['instances']:
            check(x['bbox_label'] == 0, 'unexpected native category')
            (ignored if x['ignore_flag'] else regular).append(x['bbox'])
        def boxes(q):
            return qbox2rbox(torch.tensor(q, dtype=torch.float32).reshape(-1, 8)).numpy()
        gt, ign = boxes(regular), boxes(ignored)
        annotations.append(dict(bboxes=gt, labels=np.zeros(len(gt), np.int64),
                                bboxes_ignore=ign, labels_ignore=np.zeros(len(ign), np.int64)))
    audit = dict(population_ids=ids, trainval_count=len(train), overlap=[], missing=[], extra=[],
                 xml_manifest=manifest, xml_difficult_count=xml_difficult,
                 effective_gt=sum(len(a['bboxes']) for a in annotations),
                 effective_ignore=sum(len(a['bboxes_ignore']) for a in annotations),
                 note='Installed HRSC loader ignores XML difficult flag; preserve existing loader semantics.',
                 dataset_root=str(dataset.resolve()))
    return ids, annotations, shapes, audit


def read_inputs(dataset, predictions, cfg, rebuilt=False):
    """Evaluator-only raw input validation; return label-free predictions separately."""
    ids, annotations, shapes, audit = read_native(dataset, cfg)
    frozen = cfg['input_sha256']
    prediction_only, bindings = {}, {}
    for model in cfg['models']:
        folder = predictions / model / 'clean'
        run = json.loads((folder / 'RUN.json').read_text())
        if rebuilt:
            from orientbench.r029.recover import validate_runtime
            validate_runtime(folder, dataset, cfg, model)
        else:
            for name, expected in frozen[model].items():
                check(digest(folder / name) == expected, f'changed {model}/{name}')
        check(run['model'] == model and run['split'] == 'test' and run['corruption'] == 'clean'
              and run['images'] == len(ids), 'prediction provenance mismatch')
        with (folder / 'predictions.pkl').open('rb') as f:
            records = pickle.load(f)
        keys = [str(x['img_id']) for x in records]
        check(len(keys) == len(set(keys)), 'duplicate prediction ID')
        check(set(keys) == set(ids), 'missing/extra prediction image IDs')
        by_id = dict(zip(keys, records))
        dets = []
        for image_id, annotation in zip(ids, annotations):
            r = by_id[image_id]
            check(Path(r['img_path']).resolve() == (dataset / 'images' / f'{image_id}.bmp').resolve(),
                  f'prediction image path mismatch: {image_id}')
            check(tuple(r['ori_shape']) == shapes[image_id], 'prediction image shape mismatch')
            for key, boxes_key, labels_key in [('gt_instances', 'bboxes', 'labels'),
                                             ('ignored_instances', 'bboxes_ignore', 'labels_ignore')]:
                np.testing.assert_array_equal(arr(r[key]['bboxes']), annotation[boxes_key])
                np.testing.assert_array_equal(arr(r[key]['labels']), annotation[labels_key])
            p = r['pred_instances']
            check(np.all(arr(p['labels']) == 0), 'non-ship prediction')
            d = np.column_stack((arr(p['bboxes']), arr(p['scores'])))
            check(d.dtype == np.float32 and d.shape[1] == 6 and np.isfinite(d).all(), 'invalid predictions')
            dets.append(d)
        prediction_only[model] = dets
        bindings[model] = dict(run=run, actual_sha256={name: digest(folder / name) for name in frozen[model]},
                               historical_sha256=frozen[model], rebuilt=rebuilt)
    audit.update(bindings=bindings, prediction_root=str(predictions.resolve()))
    return ids, prediction_only, annotations, audit


def build_oracle(dets, annotations, threshold):
    """Full labels stay in evaluator/oracle; simulator receives queried vectors only."""
    scores = np.concatenate([x[:, -1] for x in dets])
    order = np.argsort(-scores)  # EXACT installed evaluator input dtype/order; not stable-sort fiction.
    inverse = np.empty(len(order), dtype=np.int64)
    inverse[order] = np.arange(len(order))
    vectors, all_tp, all_fp, offset = [], [], [], 0
    for i, (d, a) in enumerate(zip(dets, annotations)):
        tp, fp = tpfp_default(d, a['bboxes'], a['bboxes_ignore'], threshold, 'rbox')
        # Independent r028 trace, restored to original prediction positions before global ordering.
        rows, _ = trace_image(d, a['bboxes'], a['bboxes_ignore'], threshold, str(i))
        rows = sorted(rows, key=lambda r: r['prediction_index'])
        np.testing.assert_array_equal(tp[0], [r['tp'] for r in rows])
        np.testing.assert_array_equal(fp[0], [r['fp'] for r in rows])
        vectors.append((inverse[offset:offset + len(d)], tp[0], fp[0], len(a['bboxes'])))
        all_tp.append(tp[0]); all_fp.append(fp[0]); offset += len(d)
    cumulative_tp = np.cumsum(np.concatenate(all_tp)[order])
    cumulative_fp = np.cumsum(np.concatenate(all_fp)[order])
    gt = sum(len(a['bboxes']) for a in annotations)
    ref, details = eval_rbbox_map([[d] for d in dets], annotations, iou_thr=threshold,
                                  use_07_metric=True, box_type='rbox', logger='silent', nproc=1)
    recall = cumulative_tp / np.maximum(np.array([gt], dtype=int), np.finfo(np.float32).eps)
    precision = cumulative_tp / np.maximum(cumulative_tp + cumulative_fp, np.finfo(np.float32).eps)
    np.testing.assert_array_equal(recall, details[0]['recall'])
    np.testing.assert_array_equal(precision, details[0]['precision'])
    own, estimated_gt = estimate(vectors, np.ones(len(vectors)))
    check(estimated_gt == gt and abs(own - ref) <= 1e-7, 'census replay failure')
    return vectors, float(ref), dict(gt=gt, detections=len(order), census_plugin_ap=own,
                                   standard_ap=float(ref), delta=own - ref,
                                   per_image_tp_fp_equal=True, every_prefix_recall_precision_equal=True)


def summarize(rows, truths, cfg):
    result = []
    for threshold in cfg['iou_thresholds']:
        target = truths[str(threshold)][1] - truths[str(threshold)][0]
        for budget in cfg['budgets']:
            for method in cfg['methods']:
                selected = [r for r in rows if r['iou'] == threshold and r['budget'] == budget and r['method'] == method]
                error = np.array([r['delta'] - target for r in selected])
                result.append(dict(iou=threshold, budget=budget, method=method, true_delta=target,
                                   bias=float(error.mean()), bias_mcse=float(error.std(ddof=1) / np.sqrt(len(error))),
                                   rmse=float(np.sqrt(np.mean(error ** 2))),
                                   mae=float(np.mean(abs(error))),
                                   p90_absolute_error=float(np.quantile(abs(error), .9)),
                                   probability_within_1pp=float(np.mean(abs(error) <= cfg['absolute_error_tolerance'])),
                                   zero_estimated_gt_count=sum(r['estimated_gt'] == 0 for r in selected),
                                   sign_error_rate=(float(np.mean([np.sign(r['delta']) != np.sign(target) for r in selected]))
                                                    if abs(target) >= cfg['absolute_error_tolerance'] else None)))
    comparisons = []
    for threshold in cfg['iou_thresholds']:
        target = truths[str(threshold)][1] - truths[str(threshold)][0]
        for budget in cfg['budgets']:
            groups = {m: np.array([r['delta'] for r in rows if r['iou'] == threshold and r['budget'] == budget
                                   and r['method'] == m]) for m in cfg['methods']}
            for method in cfg['methods'][1:]:
                diff = (groups[method] - target) ** 2 - (groups['srs'] - target) ** 2
                denom = np.mean((groups['srs'] - target) ** 2)
                comparisons.append(dict(iou=threshold, budget=budget, method=method,
                                        paired_mse_difference=float(diff.mean()),
                                        mcse=float(diff.std(ddof=1) / np.sqrt(len(diff))),
                                        rmse_ratio_to_srs=float(np.sqrt(np.mean((groups[method] - target) ** 2) / denom))
                                        if denom > 1e-14 else None))
    return dict(task=cfg['task'], full_ap=truths, metrics=result, comparisons=comparisons,
                interpretation='Empirical fixed-population point-estimation feasibility, no AP confidence interval or novelty claim.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--dataset', required=True, type=Path)
    parser.add_argument('--predictions', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--rebuilt', action='store_true', help='Use r029 restored predictions, bound to the original model/config hashes')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    ids, predictions, annotations, audit = read_inputs(args.dataset, args.predictions, cfg, args.rebuilt)
    counts = np.array([sum(np.count_nonzero(predictions[m][i][:, -1] >= cfg['prediction_count_score_threshold'])
                           for m in cfg['models']) for i in range(len(ids))])
    # Freeze and persist ALL label-free query plans before computing any full-data matching/AP.
    plans = list(sample_plans(ids, counts, cfg['budgets'], cfg['replicates'], cfg['seed']))
    with (args.output / 'query_plans.jsonl').open('w') as f:
        for rep, b, method, picked, weights in plans:
            f.write(json.dumps(dict(rep=rep, budget=b, method=method, indices=picked.tolist(), weights=weights.tolist())) + '\n')
    high, low = strata(ids, counts)
    audit.update(prediction_counts=counts.tolist(), high_indices=high.tolist(), low_indices=low.tolist(),
                 numpy_version=np.__version__, python_version=platform.python_version(),
                 evaluator_sha256=digest(inspect.getsourcefile(eval_rbbox_map)),
                 hrsc_loader_sha256=digest(inspect.getsourcefile(HRSCDataset)), config_sha256=digest(args.config))
    (args.output / 'input_audit.json').write_text(json.dumps(audit, indent=2))
    oracles, truths, checks = {}, {}, {}
    for threshold in cfg['iou_thresholds']:
        truths[str(threshold)] = []
        for model in cfg['models']:
            vectors, ap, validation = build_oracle(predictions[model], annotations, threshold)
            oracles[(model, threshold)] = vectors
            truths[str(threshold)].append(ap)
            checks[f'{model}/{threshold}'] = validation
    (args.output / 'replay_checks.json').write_text(json.dumps(checks, indent=2))
    rows = []
    for rep, budget, method, picked, weights in plans:
        for threshold in cfg['iou_thresholds']:
            # The estimator sees only these queried vectors, never the full GT total or reference AP.
            values = [estimate([oracles[(m, threshold)][i] for i in picked], weights) for m in cfg['models']]
            row = dict(rep=rep, budget=budget, method=method, iou=threshold,
                       ap_a=values[0][0], ap_b=values[1][0], delta=values[1][0] - values[0][0],
                       estimated_gt=values[0][1])
            rows.append(row)
    with (args.output / 'estimates.jsonl').open('w') as f:
        for row in rows:
            f.write(json.dumps(row) + '\n')
    (args.output / 'summary.json').write_text(json.dumps(summarize(rows, truths, cfg), indent=2))
    print('r029 completed: input audit, exact prefix replay, fixed-label sampling estimates.')


if __name__ == '__main__':
    main()
