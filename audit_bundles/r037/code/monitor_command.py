#!/usr/bin/env python3
"""Run one command and record 30-second parent+children resource telemetry."""
from __future__ import annotations
import argparse, hashlib, json, subprocess, time
from pathlib import Path
import psutil

def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def family(parent: psutil.Process):
    try: return [parent,*parent.children(recursive=True)]
    except psutil.Error: return []
def sample(parent, known):
    current=family(parent); cpu=rss=0; affinity=set(); rows=[]
    for item in current:
        if item.pid not in known:
            known[item.pid]=item
            try: item.cpu_percent(None)
            except psutil.Error: pass
    procs=[known[p.pid] for p in current]
    for p in procs:
        try:
            pcpu=p.cpu_percent(None); mem=p.memory_info().rss; aff=p.cpu_affinity()
            cpu+=pcpu; rss+=mem; affinity.update(aff); rows.append({"pid":p.pid,"cpu_percent":pcpu,"rss_bytes":mem,"affinity_count":len(aff)})
        except psutil.Error: pass
    return {"timestamp":time.time(),"process_count":len(rows),"aggregate_cpu_percent":cpu,"aggregate_rss_bytes":rss,"affinity_union_count":len(affinity),"processes":rows}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); ap.add_argument("command",nargs=argparse.REMAINDER); a=ap.parse_args()
    if a.command and a.command[0]=="--": a.command=a.command[1:]
    a.output.parent.mkdir(parents=True,exist_ok=True); started=time.time()
    p=subprocess.Popen(a.command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    parent=psutil.Process(p.pid); known={}; samples=[sample(parent,known)]
    while p.poll() is None:
        time.sleep(1)
        if p.poll() is None: samples.append(sample(parent,known))
    stdout,stderr=p.communicate(); ended=time.time()
    result={"schema_version":1,"cwd":str(Path.cwd()),"argv":a.command,"start_unix":started,"end_unix":ended,"elapsed_seconds":ended-started,"exit_code":p.returncode,"stdout_sha256":digest(stdout),"stderr_sha256":digest(stderr),"stdout_bytes":len(stdout),"stderr_bytes":len(stderr),"sampling_period_seconds":1,"meets_30_second_cadence":True,"samples":samples}
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    if p.returncode: raise SystemExit(p.returncode)
if __name__=="__main__": main()
