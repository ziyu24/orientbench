"""angle_version verification PLAN (no formal conclusion).

Enumerates the checks required to confirm angle conventions across datasets,
models, and predictions, based on the config audit + GT parser + prediction
schema. Items that cannot yet be confirmed stay 'uncertain' — nothing is
fabricated.
"""
from __future__ import annotations

from typing import Any, Dict, List

ANGLE_CHECKS: List[Dict[str, str]] = [
    {"check_id": "dota_le90_sign", "scope": "DOTA-v1.0/v1.5 GT",
     "method": "poly8 -> cv2.minAreaRect -> theta; cross-check sign vs mmrotate poly2obb_le90 on a sample",
     "current_status": "uncertain", "blocking_for": "DOTA angle-error gate"},
    {"check_id": "dior_le90_sign", "scope": "DIOR-R GT",
     "method": "robndbox corners -> minAreaRect vs raw <angle>; compare sign/range",
     "current_status": "uncertain", "blocking_for": "DIOR angle-error gate"},
    {"check_id": "fair1m_le90_sign", "scope": "FAIR1M-v1.0 GT",
     "method": "points polygon -> minAreaRect; verify le90 range/sign on a sample",
     "current_status": "uncertain", "blocking_for": "FAIR1M angle-error gate"},
    {"check_id": "hrsc_mbox_le90_equiv", "scope": "HRSC2016 GT",
     "method": "mbox_ang (rad) vs le90: confirm convention & sign; visual + numeric on sample",
     "current_status": "uncertain", "blocking_for": "HRSC angle-error gate (highest priority)"},
    {"check_id": "prediction_theta_unit", "scope": "prediction ingestion",
     "method": "confirm each real prediction theta is radians & le90 (angle_unit/angle_version fields)",
     "current_status": "uncertain", "blocking_for": "any real-prediction angle gate"},
    {"check_id": "minarearect_normalization", "scope": "Bench-Core geometry",
     "method": "verify poly8_to_obb le90 normalization [-pi/2,pi/2) matches detector convention",
     "current_status": "derived_unverified", "blocking_for": "GT<->pred angle alignment"},
]


def build_angle_version_plan(angle_audit_summary: Dict[str, Any] = None) -> Dict[str, Any]:
    rows = [dict(c) for c in ANGLE_CHECKS]
    n_uncertain = sum(1 for r in rows if r["current_status"].startswith("uncertain")
                      or "unverified" in r["current_status"])
    return {
        "n_checks": len(rows), "n_uncertain": n_uncertain,
        "all_resolved": n_uncertain == 0,
        "note": "GV-obliquity is sign-invariant (unaffected); angle-error gate IS affected.",
        "checks": rows,
    }
