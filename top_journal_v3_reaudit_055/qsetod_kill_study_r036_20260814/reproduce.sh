#!/usr/bin/env bash
set -euo pipefail
project_root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$project_root"
conda run -n pcp-obb python top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/verify_bundle_manifest.py --bundle audit_bundles/r036
conda run -n pcp-obb python audit_bundles/r036/code/validate_r036.py --project "$project_root" --persistent audit_bundles/r036 --execution audit_bundles/r036/execution
