"""One-shot entry for corrected complete-image M3 risk control.

This delegates to :mod:`m3_image_level_risk`, which validates full-val lineage
and the immutable frozen-protocol hash before replacing any result. It exits
nonzero on a missing/partial input and never falls back to matched-image-only
or instance-i.i.d. formal guarantees.
"""
import sys
sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m3_image_level_risk as m3

if __name__ == "__main__":
    try:
        m3.run()
    except m3.InputValidationError as exc:
        m3.lg(f"M3_INPUT_VALIDATION_FAILED: {exc}")
        raise SystemExit(str(exc))
