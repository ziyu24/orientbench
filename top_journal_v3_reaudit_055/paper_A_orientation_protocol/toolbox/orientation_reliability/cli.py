from __future__ import annotations
import argparse,csv,json
import numpy as np
from .core import nrc,aurc,certify_alpha_frontier

def main():
    p=argparse.ArgumentParser();p.add_argument("csv");p.add_argument("--score",default="score");p.add_argument("--risk",default="risk");p.add_argument("--severe",default="severe");p.add_argument("--scene",default="scene_id");p.add_argument("--ap75",type=float,required=True);a=p.parse_args()
    r=list(csv.DictReader(open(a.csv)));s=np.array([float(x[a.score]) for x in r]);risk=np.array([float(x[a.risk]) for x in r]);sev=np.array([int(x[a.severe]) for x in r]);scene=np.array([x[a.scene] for x in r])
    front=certify_alpha_frontier(s,sev,scene);point=next((x for x in front if x["status"]=="CERTIFIED"),None)
    print(json.dumps({"AP75":a.ap75,"detection_score_NRC":nrc(s,risk),"AURC":aurc(s,risk),"scene_risk_workpoint":point or "INFEASIBLE","frontier":front},indent=2))
if __name__=="__main__":main()
