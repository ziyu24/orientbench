"""Fail-closed r013 H1a adjudicator from sealed raw evidence and independent verifier."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--models',type=Path,required=True);p.add_argument('--stats',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();s=json.load(open(a.stats/'summary.json'));v=json.load(open(a.stats/'verify.json'))
 valid=v['independent'] and v['matches_summary'] and v['mutation_all_pass'] and s['all_heads_nonconstant'] and v['all_heads_nonconstant'] and all(x<.5 for x in s['clean_simultaneous_upper'])
 upper=s['simultaneous_upper'];power=s['power']
 if not valid:status,reason='INCONCLUSIVE_R013_H1A','IMPLEMENTATION_OR_UTILITY'
 elif any(x<.020 for x in upper):status,reason='KILL_R013_H1A','SIMULTANEOUS_UPPER_BELOW_2PP'
 elif any(x<.80 for x in power):status,reason='INCONCLUSIVE_R013_H1A','POWER'
 elif not(all(x>=.020 for x in s['delta']) and all(x>0 for x in s['simultaneous_lower'])):status,reason='KILL_R013_H1A','EFFECT_GATE'
 else:status,reason='PASS_R013_H1A','ALL_GATES'
 models=[{'name':x.name,'sha256':sha(x)} for x in sorted(a.models.glob('*.pt'))]
 a.out.write_text(json.dumps({'protocol':'r013-h1a-v1','status':status,'reason':reason,'models':models,'statistics_sha256':sha(a.stats/'summary.json'),'verifier_sha256':sha(a.stats/'verify.json'),'calibration_only':True,'test_pixels_opened':False,'test_model_forward':False,'test_performance_computed':False},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
