#!/usr/bin/env python3
"""Independent schema and mutation validator for CMR final detections."""
from __future__ import annotations

import argparse
import copy
import pickle
from pathlib import Path

import torch

UID_STRIDE = 1_000_000_000
REQUIRED = ('candidate_uid', 'cmr_q', 'cmr_native_risk', 'cmr_original_box',
            'cmr_refined_box', 'cmr_source_row', 'cmr_rpn_level_id',
            'cmr_rpn_cell_id', 'cmr_rpn_proposal_id')


def tensor(value):
    return (value.tensor if hasattr(value, 'tensor') else value).detach().cpu()


def records_from_pickle(path: Path):
    payload = pickle.load(path.open('rb'))
    for item in payload:
        if isinstance(item, dict):
            yield item['pred_instances']
        else:
            yield item.pred_instances


def validate_instance(instance) -> None:
    for key in REQUIRED:
        if key not in instance:
            raise ValueError(f'missing required CMR field: {key}')
    n = len(instance)
    q, uid = tensor(instance.cmr_q).float(), tensor(instance.candidate_uid).long()
    risk = tensor(instance.cmr_native_risk).float()
    if q.shape != (n, 12) or risk.shape != (n,) or uid.shape != (n,):
        raise ValueError('CMR q/risk/candidate_uid shape mismatch')
    if not torch.isfinite(q).all() or not torch.isfinite(risk).all() or not torch.allclose(q.sum(-1), torch.ones(n), atol=1e-5):
        raise ValueError('invalid CMR posterior or risk')
    for key in ('cmr_original_box', 'cmr_refined_box'):
        if tensor(getattr(instance, key)).shape != (n, 5):
            raise ValueError(f'{key} shape mismatch')
    level, cell = tensor(instance.cmr_rpn_level_id).long(), tensor(instance.cmr_rpn_cell_id).long()
    source, proposal = tensor(instance.cmr_source_row).long(), tensor(instance.cmr_rpn_proposal_id).long()
    if any(x.shape != (n,) for x in (level, cell, source, proposal)):
        raise ValueError('CMR provenance component shape mismatch')
    if not torch.equal(uid, level * UID_STRIDE + cell):
        raise ValueError('candidate_uid does not match immutable level/cell provenance')
    if uid.numel() != torch.unique(uid).numel():
        raise ValueError('duplicate final candidate_uid')
    if (source < 0).any() or (proposal < 0).any():
        raise ValueError('negative proposal provenance index')


def run_mutations(instance) -> dict:
    """Each destructive provenance mutation must be rejected by the validator."""
    if len(instance) < 2:
        raise ValueError('need at least two final detections for provenance mutations')
    mutations = {}
    cases = {
        'delete_candidate_uid': lambda x: x.pop('candidate_uid'),
        'swap_level': lambda x: setattr(x, 'cmr_rpn_level_id', x.cmr_rpn_level_id.flip(0)),
        'swap_cell': lambda x: setattr(x, 'cmr_rpn_cell_id', x.cmr_rpn_cell_id.flip(0)),
        'duplicate_candidate': lambda x: setattr(x, 'candidate_uid', torch.cat([x.candidate_uid[:1], x.candidate_uid[:1], x.candidate_uid[2:]])),
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
        validate_instance(instance); seen += len(instance)
        if mutation is None and len(instance) >= 2:
            mutation = run_mutations(instance)
    if not seen or mutation is None:
        raise RuntimeError('insufficient final CMR detections for schema/mutation validation')
    args.out.write_text(str({'status': 'PASS', 'final_detections': seen, 'mutations': mutation}) + '\n')


if __name__ == '__main__':
    main()
