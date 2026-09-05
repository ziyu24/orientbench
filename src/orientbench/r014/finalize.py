"""Fail-closed r014 correction-only adjudicator."""
from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();r=a.root;s=json.load(open(r/'source_audit/summary.json'));g=json.load(open(r/'geometry_reference.json'));st=json.load(open(r/'statistics/summary.json'));v=json.load(open(r/'statistics/verify.json'));m=json.load(open(r/'mutations.json'))
 valid=(s['train_eligible']==4065 and s['calibration_eligible']==7416 and s['old_actual_canvas_changed']['train']==0 and s['old_actual_canvas_changed']['calibration']==2318 and g['eligible_geometry_mismatch_count']==0 and g['reference_pixel_nonzero_difference_count']==0 and v['matches_primary'] and v['probabilities_valid'] and m['all_pass'] and st['all_heads_nonconstant'] and max(st['clean_simultaneous_upper'])<.5)
 if not valid:status,reason='INCONCLUSIVE_R013_H1A','INPUT_OR_IMPLEMENTATION'
 elif any(x<.02 for x in st['simultaneous_upper']):status,reason='KILL_R013_H1A','UPPER_BELOW_2PP'
 elif any(x<.8 for x in st['power']):status,reason='INCONCLUSIVE_R013_H1A','POWER'
 elif not(all(x>=.02 for x in [q for z in st['delta'] for q in z]) and all(x>0 for x in st['simultaneous_lower'])):status,reason='KILL_R013_H1A','EFFECT_GATE'
 else:status,reason='PASS_R013_H1A','ALL_GATES'
 (r/'final.json').write_text(json.dumps({'protocol':'r014-correction-only-v1','status':status,'reason':reason,'valid':valid,'affected_calibration_eligible':s['affected']['calibration'],'test_opened':False,'models_retrained':False},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
