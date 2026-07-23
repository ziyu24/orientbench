#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /home/rspip/anaconda3/envs/mr_dev1x/bin/python \
  "$ROOT/common/app.py" --slot A --task-set m600_plus_recheck --port 17801
