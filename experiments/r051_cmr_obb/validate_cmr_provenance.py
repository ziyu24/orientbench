#!/usr/bin/env python3
"""Independent schema and mutation validator for CMR final detections."""
from __future__ import annotations

import argparse
import copy
import pickle
from pathlib import Path

import torch

UID_STRIDE = 1_000_000_000
NUM_CLASSES = 15
REQUIRED = ('candidate_uid', 'cmr_q', 'cmr_native_risk', 'cmr_original_box',
            'cmr_refined_box', 'cmr_source_row', 'cmr_rpn_level_id',
            'cmr_rpn_cell_id', 'cmr_rpn_proposal_id', 'cmr_nms_kept_index',
            'cmr_nms_class', 'cmr_rpn_candidate_uid')


def tensor(value):
    return (value.tensor if hasattr(value, 'tensor') else value).detach().cpu()


def field(instance, key):
    return instance[key] if isinstance(instance, dict) else getattr(instance, key)


def replace_field(instance, key, value):
    if isinstance(instance, dict):
        instance[key] = value
    else:
        setattr(instance, key, value)


def swap_or_tamper(instance, key):
    """Exchange two distinct persisted rows; make a non-noop tamper otherwise."""
    value = field(instance, key).clone()
    different = (value != value[0]).nonzero(as_tuple=False).flatten()
    if len(different):
        j = int(different[0]); value[0], value[j] = value[j].clone(), value[0].clone()
    else:
        value[0] += 1
    replace_field(instance, key, value)


def records_from_pickle(path: Path):
    payload = pickle.load(path.open('rb'))
    for item in payload:
        if isinstance(item, dict):
            yield item['pred_instances']
        else:
            yield item.pred_instances


def validate_instance(instance) -> None:
    # Empty images have no final detection provenance to validate.  Their
    # schema may legitimately omit auxiliary fields after the host empty-NMS
    # path; nonempty images remain subject to every invariant below.
    if 'bboxes' in instance and len(field(instance, 'bboxes')) == 0:
        return
    for key in REQUIRED:
        if key not in instance:
            raise ValueError(f'missing required CMR field: {key}')
    q, uid = tensor(field(instance, 'cmr_q')).float(), tensor(field(instance, 'candidate_uid')).long()
    n = len(uid)
    risk = tensor(field(instance, 'cmr_native_risk')).float()
    if q.shape != (n, 12) or risk.shape != (n,) or uid.shape != (n,):
        raise ValueError('CMR q/risk/candidate_uid shape mismatch')
    if not torch.isfinite(q).all() or not torch.isfinite(risk).all() or not torch.allclose(q.sum(-1), torch.ones(n), atol=1e-5):
        raise ValueError('invalid CMR posterior or risk')
    for key in ('cmr_original_box', 'cmr_refined_box'):
        if tensor(field(instance, key)).shape != (n, 5):
            raise ValueError(f'{key} shape mismatch')
    level, cell = tensor(field(instance, 'cmr_rpn_level_id')).long(), tensor(field(instance, 'cmr_rpn_cell_id')).long()
    source, proposal = tensor(field(instance, 'cmr_source_row')).long(), tensor(field(instance, 'cmr_rpn_proposal_id')).long()
    kept = tensor(field(instance, 'cmr_nms_kept_index')).long()
    nms_class = tensor(field(instance, 'cmr_nms_class')).long()
    rpn_uid = tensor(field(instance, 'cmr_rpn_candidate_uid')).long()
    if any(x.shape != (n,) for x in (level, cell, source, proposal, kept, nms_class, rpn_uid)):
        raise ValueError('CMR provenance component shape mismatch')
    if not torch.equal(rpn_uid, level * UID_STRIDE + cell):
        raise ValueError('RPN candidate UID does not match immutable level/cell provenance')
    if not torch.equal(uid, rpn_uid * NUM_CLASSES + nms_class):
        raise ValueError('decoded proposal/class UID does not match immutable provenance')
    if uid.numel() != torch.unique(uid).numel():
        raise ValueError('duplicate final candidate_uid')
    if (source < 0).any() or (proposal < 0).any():
        raise ValueError('negative proposal provenance index')
    if not torch.equal(source, torch.div(kept, NUM_CLASSES, rounding_mode='floor')):
        raise ValueError('NMS kept index does not point to exported proposal source row')
    if not torch.equal(nms_class, torch.remainder(kept, NUM_CLASSES)):
        raise ValueError('NMS kept index does not point to exported class row')
    if not torch.equal(nms_class, tensor(field(instance, 'labels')).long()):
        raise ValueError('NMS class mapping does not match final detection label')


def run_mutations(instance) -> dict:
    """Each destructive provenance mutation must be rejected by the validator."""
    if len(field(instance, 'candidate_uid')) < 2:
        raise ValueError('need at least two final detections for provenance mutations')
    mutations = {}
    cases = {
        'delete_candidate_uid': lambda x: x.pop('candidate_uid'),
        'swap_level': lambda x: swap_or_tamper(x, 'cmr_rpn_level_id'),
        'swap_cell': lambda x: swap_or_tamper(x, 'cmr_rpn_cell_id'),
        'swap_nms_mapping': lambda x: swap_or_tamper(x, 'cmr_nms_kept_index'),
        'duplicate_candidate': lambda x: replace_field(x, 'candidate_uid', torch.cat([field(x, 'candidate_uid')[:1], field(x, 'candidate_uid')[:1], field(x, 'candidate_uid')[2:]])),
    }
    for name, mutate in cases.items():
        trial = copy.deepcopy(instance)
        try:
            mutate(trial); validate_instance(trial)
        except (ValueError, KeyError, AttributeError):
            mutations[name] = 'rejected'
        else:
            raise AssertionError(f'validator accepted mutation {name}')
    return mutations


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--predictions', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); seen = 0; mutation = None
    for instance in records_from_pickle(args.predictions):
        validate_instance(instance); seen += len(field(instance, 'candidate_uid'))
        if mutation is None and len(field(instance, 'candidate_uid')) >= 2:
            mutation = run_mutations(instance)
    if not seen or mutation is None:
        raise RuntimeError('insufficient final CMR detections for schema/mutation validation')
    args.out.write_text(str({'status': 'PASS', 'final_detections': seen, 'mutations': mutation}) + '\n')


if __name__ == '__main__':
    main()
