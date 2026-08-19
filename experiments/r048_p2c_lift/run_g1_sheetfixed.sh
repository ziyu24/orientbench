#!/usr/bin/env bash
# Reproducible val-only selection and jitter for the corrected same-r048 run.
set -euo pipefail
root="outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819"
formal="$root/formal_sheetfixed"
out="$root/g1_val_sheetfixed"
mkdir -p "$out"
eval_one() {
  local tag="$1" kind="$2" checkpoint="$3" jitter="${4:-0}" hid="${5:-384}" layers="${6:-3}"
  CUDA_VISIBLE_DEVICES=3 python experiments/r048_p2c_lift/evaluate_g1_val.py --kind "$kind" --checkpoint "$checkpoint" --jitter "$jitter" --hid "$hid" --layers "$layers" --out "$out/${tag}.json" >"$out/${tag}.log" 2>&1
}
eval_one p2c_small P2C_LIFT "$formal/p2c_small/best.pt" 0 256 2
eval_one p2c_base P2C_LIFT "$formal/p2c_base/best.pt" 0 384 3
eval_one p2c_wide P2C_LIFT "$formal/p2c_wide/best.pt" 0 512 3
eval_one whole_crop_binary WHOLE_CROP_BINARY "$formal/whole_crop_binary/best.pt"
eval_one concat_endpoint_binary CONCAT_ENDPOINT_BINARY "$formal/concat_endpoint_binary/best.pt"
eval_one headpoint_2d HEADPOINT_2D "$formal/headpoint_2d/best.pt"
eval_one direct_s1_vm DIRECT_S1_VM "$formal/direct_s1_vm/best.pt"
python - "$out" <<'PY'
import json,sys
from pathlib import Path
o=Path(sys.argv[1])
def metric(name): return json.loads((o/(name+'.json')).read_text())['metrics']
def choose(names):
 return min(names,key=lambda n:(-metric(n)['accuracy'],metric(n)['augrc'],metric(n)['mean_circular_error_deg'],n))
p2c=choose(['p2c_small','p2c_base','p2c_wide'])
baseline=choose(['whole_crop_binary','concat_endpoint_binary','headpoint_2d','direct_s1_vm'])
(o/'selection.json').write_text(json.dumps({'schema_version':2,'selection_order':['max_accuracy','min_AUGRC','min_mean_circular_error','fixed_name'],'p2c':p2c,'baseline':baseline},indent=2))
PY
read selected baseline < <(python - "$out/selection.json" <<'PY'
import json,sys
x=json.load(open(sys.argv[1]));print(x['p2c'],x['baseline'])
PY
)
case "$selected" in p2c_small) pkind=P2C_LIFT; phid=256; players=2;; p2c_base) pkind=P2C_LIFT; phid=384; players=3;; p2c_wide) pkind=P2C_LIFT; phid=512; players=3;; esac
case "$baseline" in whole_crop_binary) bkind=WHOLE_CROP_BINARY;; concat_endpoint_binary) bkind=CONCAT_ENDPOINT_BINARY;; headpoint_2d) bkind=HEADPOINT_2D;; direct_s1_vm) bkind=DIRECT_S1_VM;; esac
for j in 5 10 15; do
  eval_one "${selected}_jitter_${j}" "$pkind" "$formal/$selected/best.pt" "$j" "$phid" "$players"
  eval_one "${baseline}_jitter_${j}" "$bkind" "$formal/$baseline/best.pt" "$j"
done
