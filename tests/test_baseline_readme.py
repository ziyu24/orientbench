"""Focused tests for orientbench.io.baseline_readme.

Covers: markdown table extraction, valid bool normalization, markdown link
path extraction, numeric conversion (incl. bold-wrapped / failure cases),
metadata join, and missing-field tolerance.

Runnable via ``pytest`` or directly ``python tests/test_baseline_readme.py``.
"""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.baseline_readme import (  # noqa: E402
    extract_link,
    extract_tables,
    infer_stack_env,
    normalize_valid,
    parse_baseline_readme,
    to_float,
    to_int,
)

# A minimal synthetic readme exercising the two joined tables + edge cases.
SYNTH = """# header

## main

| # | model_id | dataset | train/val | epoch_best | mAP_best | valid | pth | log | config | source |
|---|---|---|---|---:|---:| --- |---|---|---|---|
| 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | train→val | 11 | **0.7061** | valid | [a.pth](baseline_x/DOTA10/a.pth) | [t.log](baseline_x/DOTA10/t.log) | [config.py](baseline_x/DOTA10/config.py) | /some/source/path |
| 2 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.5 | train→val | n/a | bad | invalid | [b.pth](baseline_y/b.pth) | no-link-log | [c.py](baseline_y/c.py) | iev (see [README](baseline_y/README.md)) |

## 详细 metadata

| # | model | dataset | actual_gb | per_gpu_bs | gpus | actual_lr | optimizer | scheduler | angle | metric | eval_interval | special |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|---|
| 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | **8** | 2 | 4 | **0.02** | SGD | step | le90 | DOTAMetric | 1 epoch | ok |
"""


def test_extract_tables_count_and_shape():
    tables = extract_tables(SYNTH)
    assert len(tables) == 2
    main = tables[0]
    assert main.headers[1] == "model_id"
    assert len(main.rows) == 2
    meta = tables[1]
    assert "actual_gb" in [h.strip() for h in meta.headers]
    assert len(meta.rows) == 1


def test_normalize_valid():
    assert normalize_valid("valid") == (True, None)
    assert normalize_valid("invalid") == (False, None)
    assert normalize_valid("**valid**") == (True, None)
    assert normalize_valid("✓")[0] is True
    val, warn = normalize_valid("???")
    assert val is None and warn is not None


def test_extract_link():
    assert extract_link("[a.pth](baseline_x/a.pth)") == ("a.pth", "baseline_x/a.pth")
    # no link -> (None, raw)
    assert extract_link("no-link-log") == (None, "no-link-log")
    # first link wins even with trailing parenthetical text
    text, target = extract_link("iev (see [README](baseline_y/README.md))")
    assert target == "baseline_y/README.md"
    assert extract_link("") == (None, None)


def test_numeric_conversion():
    assert to_int("11") == (11, None)
    assert to_int("**8**") == (8, None)
    assert to_int("9.0") == (9, None)
    bad, warn = to_int("n/a")
    assert bad == "n/a" and warn is not None
    assert to_float("**0.02**") == (0.02, None)
    badf, warnf = to_float("bad")
    assert badf == "bad" and warnf is not None


def test_infer_stack_env():
    stack, env, w = infer_stack_env("arsdetr_r50_fpn_36e_le90")
    assert env == "ars" and w is None
    stack, env, w = infer_stack_env("oriented_rcnn_lsknet_s_fpn_1x_le90")
    assert env == "pcp-obb-soda"
    stack, env, w = infer_stack_env("rotated_rtmdet_s_fpn_3x_le90")
    assert stack == "unknown" and env == "unknown" and w is not None


def test_parse_synthetic(tmp_path):
    p = tmp_path / "readme.md"
    p.write_text(SYNTH, encoding="utf-8")
    res = parse_baseline_readme(str(p), str(tmp_path), check_existence=True)
    assert res.n_total == 2
    assert res.n_valid == 1

    r1 = res.records[0]
    assert r1["id"] == 1
    assert r1["valid"] is True
    assert r1["mAP_best"] == 0.7061
    assert r1["epoch_best"] == 11
    # relative preserved, absolute resolved under root
    assert r1["pth"] == "baseline_x/DOTA10/a.pth"
    assert r1["pth_abs"].endswith("baseline_x/DOTA10/a.pth")
    assert os.path.isabs(r1["pth_abs"])
    # metadata joined
    assert r1["actual_gb"] == 8
    assert r1["actual_lr"] == 0.02
    assert r1["optimizer"] == "SGD"
    assert r1["env"] == "pcp-obb"
    # files don't exist on disk -> exists flags False, but valid untouched
    assert r1["pth_exists"] is False
    assert r1["inference_ready"] is True

    r2 = res.records[1]
    assert r2["valid"] is False
    # bad numerics fall back to raw + warnings recorded
    assert r2["epoch_best"] == "n/a"
    assert r2["mAP_best"] == "bad"
    assert any("int" in w for w in r2["warnings"])
    # invalid -> inference_ready False regardless of links
    assert r2["inference_ready"] is False
    # log cell had no markdown link -> kept as raw text target
    assert r2["log"] == "no-link-log"


def test_missing_metadata_tolerated(tmp_path):
    # main table only, no metadata table
    only_main = "\n".join(SYNTH.splitlines()[:8])
    p = tmp_path / "r.md"
    p.write_text(only_main, encoding="utf-8")
    res = parse_baseline_readme(str(p), str(tmp_path), check_existence=False)
    assert res.n_total >= 1
    r1 = res.records[0]
    # metadata fields fall back to None / "unknown"
    assert r1["actual_gb"] is None
    assert r1["optimizer"] == "unknown"


def _run_all():
    import tempfile
    import types

    class _TmpPath:
        def __init__(self, d):
            self._d = d

        def __truediv__(self, name):
            return types.SimpleNamespace(
                write_text=lambda text, encoding="utf-8": open(
                    os.path.join(self._d, name), "w", encoding=encoding
                ).write(text),
                __str__=lambda self_=None: os.path.join(self._d, name),
            )

    passed = 0
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
                    with tempfile.TemporaryDirectory() as d:
                        # provide a pathlib-like object
                        import pathlib

                        fn(pathlib.Path(d))
                else:
                    fn()
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
