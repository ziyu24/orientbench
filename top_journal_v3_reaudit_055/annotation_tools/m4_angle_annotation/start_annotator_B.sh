#!/usr/bin/env bash
set -Eeuo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
exec bash "$ROOT/start_annotator_B_m600.sh"
