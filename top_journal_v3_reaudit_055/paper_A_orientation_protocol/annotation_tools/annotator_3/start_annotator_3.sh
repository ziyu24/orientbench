#!/usr/bin/env bash
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$R/common/app.py" --slot 3 --port 17803
