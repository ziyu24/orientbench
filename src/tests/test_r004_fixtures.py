from orientbench.r004.fixtures import run


def test_r004_synthetic_fixtures(tmp_path):
    assert run(tmp_path / "fixtures.json")["passed"]
