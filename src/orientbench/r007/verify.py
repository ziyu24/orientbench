"""Independent r007 candidate census; does not import qualification."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOTS = (("rsdd_sar", "GF-3_or_TerraSAR-X", ("RSDD-SAR", "RSDD", "rsdd")),
         ("sar_aircraft", "SAR-AIRcraft-1.0", ("SAR-AIRcraft-1.0", "SAR-AIRcraft", "sar_aircraft")))


def canonical(x): return x % 180.0
def distance(a, b):
    d = abs(canonical(a)-canonical(b)); return min(d, 180.0-d)


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--dataset-root",type=Path,required=True); p.add_argument("--primary",type=Path,required=True); p.add_argument("--out",type=Path,required=True); a=p.parse_args()
    primary=json.loads(a.primary.read_text()); records=[]
    for name,platform,names in ROOTS:
        found=next((a.dataset_root/x for x in names if (a.dataset_root/x).is_dir()),None)
        records.append({"candidate":name,"claimed_platform":platform,"local_root":str(found) if found else None,"root_present":found is not None,"reason_codes":["LOCAL_SAR_ASSET_ABSENT"] if found is None else ["RAW_METADATA_PARSER_REQUIRED"]})
    expected=[{"candidate":x["candidate"],"claimed_platform":x["claimed_platform"],"local_root":x["local_root"],"root_present":x["root_present"],"reason_codes":x["reason_codes"]} for x in primary["candidates"]]
    fixtures={"pi_identity":distance(0.,180.)==0.,"right_angle":math.isclose(distance(0.,90.),90.),"mutation":distance(0.,1.)>0.}
    passed=records==expected and all(fixtures.values()) and primary["token"]=="ASSET_UNAVAILABLE_R007"
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps({"protocol":"r007-independent-asset-census-v1","records":records,"fixtures":fixtures,"passed":passed,"token":primary["token"] if passed else "INCONCLUSIVE_R007_ASSET_AUDIT"},indent=2,sort_keys=True)+"\n")


if __name__ == "__main__": main()
