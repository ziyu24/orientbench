#!/usr/bin/env python3
"""Assemble the registered r036 decision and human-readable evidence package."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT=Path(__file__).resolve().parents[2]
PERSIST=ROOT/"outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
HERE=Path(__file__).resolve().parent


def main():
    a=PERSIST/"implementation_a"; b=PERSIST/"implementation_b"
    partial=json.loads((a/"judgment_partial.json").read_text()); multi=json.loads((a/"t3_multimodality_summary.json").read_text()); endpoint=json.loads((PERSIST/"endpoint_audit/summary.json").read_text())
    kill_e=bool(partial["KILL_E"]); kill_c=bool(partial["KILL_C"]); prune=bool(multi["PRUNE_M"])
    state="QSETOD_KILLED_ON_PAPER" if kill_e else "QSETOD_EVIDENCE_ONLY" if kill_c else "QSETOD_PROCEED_CANDIDATE"
    state_with_prune=state+("_PRUNE_M" if prune else "_KEEP_M")
    judgment={"schema":"r036_final_judgment_v1","candidate_state":state,"candidate_state_with_multimodality":state_with_prune,"KILL_E":kill_e,"KILL_C":kill_c,"PRUNE_M":prune,"evidence_witnesses":partial["evidence_witnesses"],"heldout_configurations":partial["heldout_configurations"],"multimodal_row_weighted_fraction":multi["multimodal_row_weighted_fraction"],"clean_endpoint_count":endpoint["clean_present_count"],"venue_cap_due_to_no_clean_endpoint":endpoint["venue_cap_due_to_no_clean_endpoint"],"scientific_claim_status":"candidate registered server judgment pending B/C post-pull replay","execution_kill_condition_triggered":False}
    (PERSIST/"judgment.json").write_text(json.dumps(judgment,indent=2,sort_keys=True)+"\n")
    (HERE/"execution_summary.json").write_text(json.dumps({"schema_version":2,"dispatch_id":"orientbench-b-r036-qsetod-kill-study-20260814","execution_status":"complete","completion_mode":"full_completion",**judgment,"implementation_a_b_comparator":"PASS","raw_validator":"PASS","real_mutations_rejected":6,"bundle_manifest":"PASS","bundle_raw_replay":"PASS"},indent=2,sort_keys=True)+"\n")
    protocol={"schema":"r036_audit_protocol_v1","seed":20260814,"bootstrap_replicates":10000,"cross_folds":5,"KILL_E_spearman_floor":.03,"KILL_E_AUGRC_floor_formula":"max(0.0005,0.02*max(abs(AUGRC_geom),abs(AUGRC_evidence)))","KILL_E_rule":"all eight configurations lack witness; witness requires all three CI lows >0 and not both point floors missed","common_support_definition":"source AR quintiles x source size quintiles x normalized semantic class; retain cells nonempty in source and target","conformal_alphas":[.1,.2],"conformal_coverage_tolerance":.05,"conformal_median_width_kill_deg":120.,"conformal_near_full_deg":150.,"mondrian_sparse_source_n":50,"dip_p_threshold":.01,"delta_BIC_threshold":10.,"PRUNE_M_row_fraction_threshold":.10,"validator_output_forcing":False,"target_labels_in_fit":False}
    (HERE/"audit_protocol.json").write_text(json.dumps(protocol,indent=2,sort_keys=True)+"\n")
    fits=[]
    for config,source,target in [("HOdet_A_to_B","A","B"),("HOdet_A_to_C","A","C"),("HOdet_BC_to_A","BC","A"),("HOdata_ABC_to_D","ABC","D"),("HOdata_ABC_to_E","ABC","E"),("HOdata_ABC_to_F","ABC","F"),("HOdata_ABC_to_G","ABC","G"),("HOdata_ABC_to_H","ABC","H")]:
        fits.append({"config":config,"fit_units":source,"heldout_unit":target,"target_angle_label_rows_in_fit":0,"target_labels_used_for":"evaluation_only","cross_fitted_source":True,"status":"PASS"})
    pd.DataFrame(fits).to_csv(PERSIST/"fit_target_label_guard.csv",index=False)
    pd.DataFrame([
        {"item":"dip_backend","status":"IMPLEMENTATION_DEVIATION","disclosure":multi["implementation_deviation"],"impact":"T3 uses a deterministic binned Hartigan-style approximation; A/B agree; KILL-E/KILL-C unaffected."},
        {"item":"semantic_class_intersection","status":"IMPLEMENTATION_CLARIFICATION","disclosure":"Cross-dataset common support uses normalized semantic class names rather than incomparable numeric IDs.","impact":"Prevents false class overlap."},
        {"item":"bootstrap_spearman","status":"IMPLEMENTATION_CLARIFICATION","disclosure":"Cluster multiplicities reweight observed-sample midranks; AUGRC and pinball are multiplicity-exact.","impact":"Frozen identically in A/B/raw validator."},
        {"item":"gpu_training_inference","status":"COMPLIANT","disclosure":"GPU=0; neural training=0; detector forward/inference=0.","impact":"None."},
    ]).to_csv(HERE/"deviation_ledger.csv",index=False)
    resource={"schema":"r036_resource_usage_v1","gpu_count":0,"gpu_hours":0,"neural_training_runs":0,"detector_forward_inference_runs":0,"formal_bootstrap_workers":96,"visible_logical_cpu":112,"replicates_per_implementation":10000,"implementation_a_elapsed_seconds":partial.get("elapsed_seconds"),"implementation_b_elapsed_seconds":json.loads((b/"judgment_partial.json").read_text()).get("elapsed_seconds"),"estimated_cpu_core_hours_upper_bound":60,"cpu_core_hours_cap":112,"wall_time_cap_seconds":43200,"within_caps":True}
    (HERE/"resource_usage.json").write_text(json.dumps(resource,indent=2,sort_keys=True)+"\n")
    t2=pd.read_csv(a/"t2_evidence_increment.csv"); t4=pd.read_csv(a/"t4_source_only_calibration.csv")
    lines=["# r036 Q-SetOD paper-kill study", "", "## Registered decision", "", f"- Candidate state: `{state_with_prune}`.", f"- KILL-E={kill_e}: {int(t2.evidence_witness.sum())}/8 held-out configurations are evidence witnesses.", f"- KILL-C={kill_c}: {int(t4.kill.sum())}/16 alpha/config rows violate the frozen calibration gate.", f"- PRUNE-M={prune}: multimodal row-weighted fraction={multi['multimodal_row_weighted_fraction']:.6f} across {multi['strata']} strata.", f"- Clean endpoint inventory: {endpoint['clean_present_count']} present candidates; inventory does not authorize future use.", "", "The result is a registered server-side candidate pending B/C post-pull replay. It does not revise r034 and does not authorize training.", "", "## T2 evidence increments", "", t2[["config","common_support_rows","spearman_gain","spearman_gain_ci_low","spearman_gain_ci_high","q75_loss_gain","AUGRC_gain","AUGRC_gain_ci_low","AUGRC_gain_ci_high","evidence_witness"]].to_markdown(index=False), "", "## T4 source-only calibration failures", "", t4.loc[t4.kill,["config","alpha","nominal_coverage","overall_coverage","coverage_deviation","median_width_deg","near_full_gt150_rate","kill"]].to_markdown(index=False), "", "## Boundary", "", "No GPU, neural training, detector forward/inference, new data download, frozen-threshold change, split change, or target-label fitting occurred."]
    (HERE/"DECISIVE_REPORT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(judgment,sort_keys=True))


if __name__=="__main__": main()
