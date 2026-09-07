"""Evaluate the fixed holdout after an explicit native-border support amendment."""
import argparse
import time
from pathlib import Path
import urllib.request
import urllib.parse
import numpy as np
from orientbench.r017.run_pilot import _local, ROOT_URL
from orientbench.r018.evaluate import read,write,digest
from orientbench.r021.data import Assets
from orientbench.r021.forecast import Transport
from orientbench.r021.run import freeze_decisions,measure_held
from orientbench.r022.support import read_input


def load_frozen(path,calibration):
    with np.load(path,allow_pickle=False) as z:
        model=Transport(z['geometry'],z['counts'],z['pair_risk'],float(z['pi']))
        for name in ('xmean','xscale','coef','ymean'):
            setattr(model,name,z[name].copy())
        model.bias=dict(zip(z['bias_names'].tolist(),z['bias_values'].tolist()))
    if model.bias!=calibration['bias'] or digest(path)!=calibration['forecaster_sha256']:
        raise ValueError('frozen model/calibration mismatch')
    return model


class HeldAssets(Assets):
    def image(self,split,tile,view):
        if split!='held':
            raise ValueError('r022 has no development recomputation')
        path=_local(self.dataset,self.records[split,tile,view]['key'])
        v=self.manifest['held_views'].index(view)
        image,info=read_input(path,tile,[s[v] for s in self.held_shifts])
        self.support[tile+'|'+view]=info
        return image

    def acquire_images(self,splits):
        if splits!=['held']:
            raise ValueError('only fixed existing held assets are allowed')
        accepted=read(self.root/'runs/r021/artifacts/retry/input_bindings.json')['images']
        for item in self.manifest['images_to_materialize']:
            if item['split']!='held':
                continue
            self.budget()
            path=_local(self.dataset,item['key'])
            if not path.is_file() or path.stat().st_size!=item['bytes'] or digest(path)!=accepted[item['key']]:
                raise ValueError('accepted held image changed; no re-download or replacement')
            self.evidence['images'][item['key']]=accepted[item['key']]
            # Check every product before any network forward, never labels.
            self.image('held',item['tile'],item['view'])
        write(self.out/'native_support.json',self.support)

    def acquire_held_labels(self):
        if not (self.out/'decisions.json').is_file():
            raise ValueError('save all decisions before obtaining outcomes')
        ledger=[];received=0
        for tile in self.manifest['held_tiles']:
            self.budget()
            item=self.labels[tile];path=_local(self.dataset,item['key'])
            record={'key':item['key'],'received_bytes':0,'expected_bytes':item['bytes']}
            ledger.append(record)
            if path.is_file():
                if path.stat().st_size!=item['bytes']:
                    raise ValueError('existing label size mismatch')
                record.update(status='reused',sha256=digest(path))
                write(self.out/'download_ledger.json',ledger)
                continue
            if received+item['bytes']>self.cfg['download_bytes_limit']:
                raise RuntimeError('label download budget would be exceeded')
            path.parent.mkdir(parents=True,exist_ok=True)
            partial=path.with_suffix(path.suffix+'.r022.part')
            try:
                url=ROOT_URL+urllib.parse.quote(item['key'],safe='/')
                with urllib.request.urlopen(url,timeout=90) as response,partial.open('xb') as stream:
                    length=response.headers.get('Content-Length')
                    if length is not None and int(length)!=item['bytes']:
                        raise ValueError('label content length mismatch')
                    while chunk:=response.read(1<<20):
                        received+=len(chunk);record['received_bytes']+=len(chunk)
                        if received>self.cfg['download_bytes_limit'] or record['received_bytes']>item['bytes']:
                            raise RuntimeError('label download budget exceeded')
                        stream.write(chunk)
                if record['received_bytes']!=item['bytes']:
                    raise ValueError('short label transfer')
                partial.rename(path)
                record.update(status='complete',sha256=digest(path))
            except Exception:
                record['status']='failed'
                raise
            finally:
                # No recursive downloader: failed and complete bytes stay in one ledger.
                write(self.out/'download_ledger.json',ledger)


def execute(assets,manifest,cfg,out,model,calibration,shifts):
    geometry=np.array([manifest['geometry'][v]['look_xy'] for v in manifest['held_views']])
    assets.acquire_images(['held'])
    assets.forward(['held'],(1701,))
    freeze_decisions(assets,manifest['held_tiles'],geometry,shifts,model,out)
    assets.forward(['held'],(1702,))
    assets.acquire_held_labels()
    summary=measure_held(assets,manifest['held_tiles'],geometry,shifts,calibration['selected_baseline'],cfg['foreground_fraction'],out)
    assets.budget()
    resources=assets.save_evidence()
    if resources['new_forward_images']!=512:
        raise ValueError('r022 must perform exactly 512 new image forwards')
    summary.update(resources=resources,selected_baseline=calibration['selected_baseline'],
        scope=cfg['scope'],protocol_amendment=cfg['support_amendment'],
        development_reused_without_refit=True)
    primary=summary['actual_labels']['intervals_97_5']
    summary['both_coprimary_lower_bounds_positive']=all(primary[k][0]>0 for k in ('policy_gain','mae_gain'))
    write(out/'summary.json',summary)
    print({k:primary[k] for k in ('policy_gain','mae_gain')},flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=Path.cwd())
    parser.add_argument('--dataset-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--device',default='cuda:0')
    args=parser.parse_args();root,out=args.project_root.resolve(),args.out.resolve()
    if not out.is_relative_to(root/'runs/r022'):
        raise ValueError('r022 artifacts must stay in this project run')
    cfg=read(root/'configs/r022/protocol.json')
    source=root/'runs/r021/artifacts/retry'
    for name,sha in cfg['frozen_source_sha256'].items():
        if digest(source/name)!=sha:
            raise ValueError('accepted frozen development changed: '+name)
    manifest_path=root/'configs/r021/data_manifest.json'
    if digest(manifest_path)!=cfg['data_manifest_sha256']:
        raise ValueError('original region/product cohort changed')
    manifest=read(manifest_path)
    out.mkdir(parents=True,exist_ok=False)
    for name in ('forecaster.npz','calibration.json','frozen_shifts.json'):
        (out/name).write_bytes((source/name).read_bytes())
    write(out/'protocol_binding.json',{'protocol_sha256':digest(root/'configs/r022/protocol.json'),
        'manifest_sha256':digest(manifest_path),'reused_sources':cfg['frozen_source_sha256']})
    calibration=read(out/'calibration.json');shifts=read(out/'frozen_shifts.json')['held']
    model=load_frozen(out/'forecaster.npz',calibration)
    assets=HeldAssets(root,args.dataset_root.resolve(),out,manifest,cfg,args.device)
    assets.held_shifts=shifts;assets.support={}
    try:
        execute(assets,manifest,cfg,out,model,calibration,shifts)
    finally:
        assets.save_evidence()


if __name__=='__main__':
    main()
