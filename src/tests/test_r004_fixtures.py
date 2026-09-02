from orientbench.r004.fixtures import run
from orientbench.r004.fixtures_independent import run as run_independent


def test_r004_synthetic_fixtures(tmp_path):
    assert run(tmp_path / "fixtures.json")["passed"]
    assert run_independent(tmp_path / "fixtures_independent.json")["passed"]
