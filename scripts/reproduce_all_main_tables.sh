#!/usr/bin/env bash
# Command 069 reproduction entry point.
#
# This is a CPU-only table rebuild from persistent, lineage-checked inputs. It
# never trains a detector, runs detector inference, reruns K2, changes a frozen
# asset, or regenerates the already-decided PSC intervention. Those expensive
# historical products are cryptographically revalidated by the final auditor.
set -Eeuo pipefail

readonly ROOT="/home/rspip/cqc/pro/study/orientbench"
readonly PY="/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
readonly AUDITOR="scripts/m069_freeze_and_repro.py"
readonly LOG="logs/reproduce_all_main_tables_069.log"

cd "$ROOT"
mkdir -p logs reports

if [[ $# -eq 0 ]]; then
    readonly LOG073="logs/reproduce_all_main_tables_073.log"
    : > "$LOG073"
    exec > >(tee -a "$LOG073") 2>&1
    export OMP_NUM_THREADS=40
    export M069_BOOTSTRAP_WORKERS=40
    ts073() { date '+%Y-%m-%d %H:%M:%S %z'; }
    run073() {
        local name=$1
        shift
        printf '[%s] STEP_START %s\n' "$(ts073)" "$name"
        "$@"
        printf '[%s] STEP_OK %s\n' "$(ts073)" "$name"
    }
    printf '[%s] REPRO_073_START cpu_only=true training=false inference=false\n' "$(ts073)"
    run073 lineage_artifact_verification "$PY" scripts/m069_lineage_audit.py
    run073 geometry_threshold_verification "$PY" scripts/derive_delta_theta_075.py --verify-frozen
    run073 ar21_main_results "$PY" scripts/m1_ar21_unify.py
    run073 fixed_size_control "$PY" scripts/m2_g2doubleprime_ar21.py
    run073 image_level_risk_control "$PY" scripts/recompute_m3_image_level_risk_control.py
    run073 geometry_and_fixed_angle_events "$PY" scripts/m4_risk_events.py
    run073 psc_split_decision "$PY" scripts/psc_phase1.py
    run073 fair1m_third_dataset "$PY" scripts/aggregate_m4_third_dataset_070.py
    run073 human_primary_and_recheck bash scripts/run_m4_m600_analysis.sh
    run073 human_risk_integration "$PY" scripts/integrate_m4_human_073.py
    run073 final_verification "$PY" scripts/verify_073_final.py
    printf '[%s] REPRO_073_COMPLETE\n' "$(ts073)"
    exit 0
fi

if [[ "${1:-}" == "--070-machine-only" ]]; then
    if [[ $# -ne 1 ]]; then
        printf 'usage: %s [--preflight-only|--070-machine-only]\n' "$0" >&2
        exit 64
    fi
    readonly LOG070="logs/reproduce_all_main_tables_070.log"
    : > "$LOG070"
    exec > >(tee -a "$LOG070") 2>&1
    export OMP_NUM_THREADS=40
    export M069_BOOTSTRAP_WORKERS=40
    ts070() { date '+%Y-%m-%d %H:%M:%S %z'; }
    run070() {
        local name=$1
        shift
        printf '[%s] STEP_START %s\n' "$(ts070)" "$name"
        "$@"
        printf '[%s] STEP_OK %s\n' "$(ts070)" "$name"
    }
    printf '[%s] REPRO_070_MACHINE_START\n' "$(ts070)"
    run070 m4_third_dataset_aggregate "$PY" scripts/aggregate_m4_third_dataset_070.py
    run070 m4_annotation_package "$PY" scripts/package_m4_human_annotation_070.py
    run070 m4_human_merge_gate "$PY" scripts/merge_m4_human_annotations.py
    run070 m4_human_analysis_gate "$PY" scripts/analyze_m4_human_disagreement.py
    run070 m4_070_final_verification "$PY" scripts/verify_m4_command_070.py --log "$LOG070"
    printf '[%s] REPRO_070_MACHINE_COMPLETE\n' "$(ts070)"
    exit 0
fi

: > "$LOG"
exec > >(tee -a "$LOG") 2>&1
export OMP_NUM_THREADS=40
export M069_BOOTSTRAP_WORKERS=40

CURRENT_STEP="bootstrap"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S %z'
}

log() {
    printf '[%s] %s\n' "$(timestamp)" "$*"
}

record_failure() {
    local exit_code=$?
    trap - ERR
    log "REPRO_069_FAILED step=${CURRENT_STEP} exit_code=${exit_code}"
    # The auditor modes already persist their detailed failure rows. For a
    # computation-step failure, create a minimal durable NOT_FROZEN record.
    if [[ "$CURRENT_STEP" != "preflight" && "$CURRENT_STEP" != "final_validation" ]]; then
        set +e
        "$PY" "$AUDITOR" --failure "$CURRENT_STEP" --exit-code "$exit_code" --log "$LOG"
        set -e
    fi
    exit "$exit_code"
}
trap record_failure ERR

run_step() {
    local name=$1
    shift
    CURRENT_STEP="$name"
    log "STEP_START ${name}"
    "$@"
    log "STEP_OK ${name}"
}

reuse_verified() {
    local name=$1
    local reason=$2
    log "REUSED_VERIFIED ${name} ${reason}"
}

if [[ $# -gt 1 || ( $# -eq 1 && "$1" != "--preflight-only" ) ]]; then
    printf 'usage: %s [--preflight-only|--070-machine-only]\n' "$0" >&2
    exit 64
fi

log "REPRO_069_START mode=${1:-full}"

run_step "lineage_artifact_verification" "$PY" scripts/m069_lineage_audit.py

CURRENT_STEP="preflight"
"$PY" "$AUDITOR" --preflight --log "$LOG"
log "STEP_OK preflight"

if [[ "${1:-}" == "--preflight-only" ]]; then
    log "REPRO_069_PREFLIGHT_ONLY_COMPLETE"
    exit 0
fi

# Real table recomputation. Each program reads persisted predictions/matches;
# none invokes a detector evaluator, training runner, torchrun, or inference.
run_step "m4_delta_frozen_verify" "$PY" scripts/derive_delta_theta_075.py --verify-frozen
run_step "m1_ar21" "$PY" scripts/m1_ar21_unify.py
run_step "m2_fixed_size" "$PY" scripts/m2_g2doubleprime_ar21.py
run_step "m3_image_level_ltt" "$PY" scripts/recompute_m3_image_level_risk_control.py
run_step "m4_risk_events" "$PY" scripts/m4_risk_events.py
run_step "psc_phase1_aggregation" "$PY" scripts/psc_phase1.py
run_step "human_merge" "$PY" scripts/merge_m4_human_annotations.py
run_step "human_analysis" "$PY" scripts/analyze_m4_human_disagreement.py

# Command 069 explicitly forbids repeating these already-completed expensive
# jobs. The auditor below checks their schemas, hashes, lineage, and decisions.
reuse_verified "k2_angle_coder_matrix" "no_training_no_evaluation"
reuse_verified "psc_phase1_forward" "six_frozen-checkpoint_forward_artifacts_revalidated_no_inference"
reuse_verified "psc_actual_head_supplement" "six_network-coordinate_targeted_supplements_revalidated_no_inference"
reuse_verified "dcl_csl_native_endpoints" "twelve_frozen-head_geometry-endpoint_dumps_revalidated_no_inference"
reuse_verified "dota_clean_fullval" "persisted_prediction_dumps_no_inference"
reuse_verified "dior_fullval_lineage" "persisted_fullval_manifests_no_inference"

log "REPRO_069_MACHINE_CHAIN_COMPLETE"
CURRENT_STEP="final_validation"
# Seal the machine-chain log before the final auditor hashes and inventories it.
# The auditor runs quietly after sealing; all detailed rows are durable CSVs.
# A successful audit therefore cannot mutate the log after its SHA-256 is recorded.
log "REPRO_069_MACHINE_LOG_SEALED final_audit=detailed_csv"
"$PY" "$AUDITOR" --final --quiet --log "$LOG" > /dev/null
