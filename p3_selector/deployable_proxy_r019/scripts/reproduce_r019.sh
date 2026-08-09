#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PY=/home/rspip/anaconda3/envs/mr_dev1x/bin/python
cd "$ROOT"

"$PY" p3_selector/deployable_proxy_r019/tests/test_eqs_rc_r019.py
if [[ -f outputs/persistent_artifacts/orientbench_r019/post_commit_receipt.json && \
      -f outputs/persistent_artifacts/orientbench_r019/postlabel/bootstrap/replicates.parquet ]]; then
  "$PY" p3_selector/deployable_proxy_r019/scripts/validate_r019.py
else
  echo "PRELABEL_ONLY: label attach remains locked until the remote prelabel receipt exists"
fi
