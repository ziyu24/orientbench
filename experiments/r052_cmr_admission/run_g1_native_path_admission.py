#!/usr/bin/env python3
"""Execute the frozen r052 native detector-path admission check.

This is deliberately a gate runner rather than a test that fabricates a
passing provenance record.  The functional contract requires every frozen
proposal UID to survive the actual loss/decode/NMS/raw-export path.  An
inherited host ``predict_bbox`` cannot consume the r052 marginal likelihood
or preserve those fields, so that condition is decidable before G2 training.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from pathlib import Path

from mmdet.models.roi_heads.standard_roi_head import StandardRoIHead

from experiments.r052_cmr_admission.joint_api import JointOutput
from experiments.r052_cmr_admission.joint_roi_head import R052JointRoIHead


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    proposals = manifest['proposals']
    unique = len({p['proposal_uid'] for p in proposals}) == len(proposals)
    required_manifest_fields = all(
        {'proposal_uid', 'class_id', 'proposal_index', 'image_id'} <= set(p)
        for p in proposals)

    # ``predict_bbox`` resolves to the upstream method.  This is a runtime
    # object-identity check, not a name-only grep: it proves the detector
    # inference path has no r052 marginalization/provenance adapter.
    inherited_predict = R052JointRoIHead.predict_bbox is StandardRoIHead.predict_bbox
    head_source = inspect.getsource(R052JointRoIHead)
    native_inference_override = 'def predict_bbox' in head_source
    joint_output_fields = set(JointOutput.__dataclass_fields__)
    uid_payload_present = {'proposal_uid', 'class_uid', 'candidate_uid'} <= joint_output_fields

    checks = {
        'frozen_manifest_exact_1024': len(proposals) == 1024,
        'frozen_manifest_unique_proposal_uids': unique,
        'frozen_manifest_has_proposal_and_class_inputs': required_manifest_fields,
        'detector_predict_bbox_has_r052_override': native_inference_override,
        'detector_predict_bbox_is_not_host_passthrough': not inherited_predict,
        'joint_output_carries_proposal_class_candidate_uids': uid_payload_present,
    }
    failed = [name for name, ok in checks.items() if not ok]
    result = {
        'schema_version': 1,
        'gate': 'G1_FUNCTIONAL_ADMISSION',
        'status': 'KILL_CMR_IMPLEMENTATION_PRINCIPLE' if failed else 'PASS',
        'formal_token_submitted': True,
        'manifest': str(args.manifest),
        'manifest_sha256': hashlib.sha256(raw).hexdigest(),
        'proposal_count': len(proposals),
        'checks': checks,
        'failed_conjuncts': failed,
        'reason': (
            'The frozen proposal universe exists, but the actual detector '
            'inference path is still StandardRoIHead.predict_bbox and '
            'JointOutput has no immutable proposal/class/candidate UID payload. '
            'Therefore marginal class/full-box/risk and provenance cannot pass '
            'through decode, NMS, and raw export.' if failed else 'all checks passed'),
        'g2_authorized': not failed,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    args.out.with_suffix('.sha256').write_text(
        hashlib.sha256(args.out.read_bytes()).hexdigest() + '  ' + args.out.name + '\n')
    print(json.dumps({'status': result['status'], 'failed_conjuncts': failed}, sort_keys=True))


if __name__ == '__main__':
    main()
