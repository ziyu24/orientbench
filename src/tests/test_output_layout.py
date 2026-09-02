from pathlib import Path

from orientbench.io.output_policy import (
    PREDICTIONS_ROOT,
    PROJECT_ROOT,
    build_prediction_output_path,
    validate_output_path,
)


def test_prediction_outputs_are_project_local_runs():
    root = Path(PROJECT_ROOT)
    assert root.name == "orientbench"
    assert Path(PREDICTIONS_ROOT) == root / "runs" / "predictions"
    output = build_prediction_output_path("HRSC2016", "baseline", "test", "now")
    assert validate_output_path(output) == (True, None)
    assert validate_output_path(str(root / "outputs" / "bad.json"))[0] is False
