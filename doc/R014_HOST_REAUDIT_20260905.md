# r014：26主机直接只读复核与科学收口

审计时间：2026-09-05 10:08 UTC；用户明确授权B直接SSH核查26。
项目实根为`/home/rspip/cqc/study/orientbench`，审计时主机与本地均为
`8e67326fc4d383cd5e310789c8b50313fae16326`，主机tracked clean。
本次未修改服务器代码/产物、训练、运行分类器或detector，也未读取test像素或性能。
仅在CPU读取原始记录、模型内容、train/calibration缓存、公开标注、COG头和校准render。

## 1. 先纠正结论

SERVER所写“原calibration manifest不在服务器，因此训练身份链不可恢复”不成立。
B亲自找到并读取原件`runs/r013/calibration/canvases/manifest.json`。
原生成器把manifest写在canvas目录本身，新验收器却检查父目录，造成假缺失。

B也撤回“缺少统一fit manifest即足以判整个训练身份不可恢复”的判断：
六份原训练日志、六个checkpoint的protocol/架构/seed/epochs、原calibration对六模型的
内容登记、G0初始化登记以及preflight对G0和train输入的绑定均存在并可交叉核验。
这些证据不依赖某一个指定文件名，不能因为汇总清单不存在便否定它们。

**科学收口：保留INCONCLUSIVE_R013_H1A；在恢复身份链和独立核验所支持的透明重建范围内，
数值裁决为POWER，不是PASS/KILL。撤销“原校准记录丢失/训练身份必然不可恢复”这个停止理由。**
r013旧错图数值仍不是有效因果证据，修正r014也不能追认为新的前瞻盲实验。

这是B对现存原件和实际计算的独立裁决，不是宣布有缺陷的自动验收器已经修好或全面通过。
本轮到此停止，不追加同路线repair/训练/推理，不打开test。当前任务单清为NO_ACTIVE_TASK；
下一步创新设计属于B科学工作，不能让工程验收循环替代新科学问题。

## 2. 找到的原始证据与精确对应

原字段、校验值、时间和完整六份epoch日志另存`doc/R014_HOST_RECORDS_20260905.json`。
该文件明确保存原件的选定字段，不伪称完整输入manifest副本；全部行仍在主机原件，
以下全行比较已由B直接完成。

| 原件/核验 | B直接核查结果 |
| --- | --- |
| calibration manifest | 7,416行/7,416唯一对象；原件SHA256为4e6aa2698dd6087175e8e61f453dcf6c2aea7d532f855cb609a4c28ae4f46be8 |
| preflight→G0 primary/final | 两个原内容摘要均匹配当前原文件 |
| preflight→train manifest | 原摘要匹配；4,065行 |
| G0→两种初始化权重 | 当前原权重与G0登记均匹配 |
| 六个checkpoint→calibration manifest | 6/6完整文件内容摘要一致 |
| 六个checkpoint内部元数据 | 均为r013-h1a-v1，对应架构/1201–1203，epochs=8 |
| 六份独立fit日志 | 每份均完整记录epoch 1至8、loss_finite=true |
| checkpoint张量 | R50各324、ViT各156；全部有限 |
| 原train canvas→原manifest | 4,065/4,065文件摘要一致 |
| 原calibration canvas→原manifest | 7,416/7,416文件摘要一致 |
| 官方GeoJSON+冻结split→原训练/校准集合 | 逐键完全相同，两集交集为0 |

初始化登记的完整摘要为：
ResNet-50 `11ad3fa62ca79e40addfd354a8ec4b7c75143b3038b8d2a807fbc68deab379ca`；
ViT-B/16 `c867db91d3e12c6cbadabb610d73c24a546bf82d8c03a9fea34f43a712ddb0e9`。
训练仍是5,370→4,068旧Public_Train=1→4,065，未把原flag=0的1,302个对象混入。

现存mtime与记录自洽：六模型完成时间为02:56:00至03:24:41 UTC，
原calibration manifest为03:31:30 UTC。mtime仅作为一致性佐证，不是不可篡改时序证明。
原RUN.json记录的是preflight命令，不是六次fit的完整执行追踪，不能拿run token替代训练记录。

为什么统一fit清单可能不存在：`train_six.main`会写汇总manifest，但实际仓库另有
`fit_one`入口，它调用相同fit函数而不写汇总清单。现存六份单fit日志与该入口相容；
没有取得完整原命令日志，不将“实际一定用了fit_one”写成已证事实。

## 3. 原始来源、属性与几何独立核查

B不导入G0主计算函数，从官方metadata恢复loc–CAT–image_id，
从官方GeoJSON重新生成三个属性标签，按既有lexical calibration component赋组。
六个raw表的全部7,416行均与官方标签及原分组一致。

直接读取87个校准影像COG头：均为地理坐标、EPSG:4326。
逐对象将GeoJSON投影到像素并独立计算最小旋转矩形，
center、L/S和RP1 theta在1e-8内零不一致，来源绑定零不一致。
本轮不读test像素；其分区名称只用于既有边界核查。

SERVER第二路径的7,416行像素表已公开、对象集合与raw相同、报告差异0；
B本次另行验证原train/calibration缓存与其原清单的全部文件内容，而不把摘要重算说成
又从COG读取了全部11,481个对象像素。已发布source修正记录的2,318错源计数保持不变。
训练227个CAT碰撞标记仍不代表227个训练错图。

## 4. B实际执行了遗漏的render检查，而不是要求再派任务

只提取已发布production render函数，在CPU调用，未构建或运行任何分类器。
用独立float64坐标参考检查87个来源的clean、−10°、+10°各两视图；
补做theta+180°视图交换、w/h+90°经long-side canonicalization，以及混合side批次检查。

| 检查 | 观测最大差/响应 |
| --- | ---: |
| production float32像素 vs 独立float64 reference | 1.996682625249324e-5 |
| theta+180°视图成对交换 | 3.600120544433594e-5 |
| w/h+90°后long-side规范化 | 0 |
| 混合尺寸batch vs 单对象render | 8.07642936706543e-6 |
| 87来源最小−10°像素响应 | 0.3535011410713196 |
| 87来源最小+10°像素响应 | 0.3592044413089752 |

这些是事后重建检查，不回填为事前门；不证明所有CPU/GPU数值路径逐bit相同。
差异在已公开5e-5重建参考界内，未发现足以改变裁剪语义的错误。
w/h等价测试明确在输入规范化后比较，不要求未canonical的参数直接等价。

## 5. 自动验收器的限制，不再与科学结论混同

`independent_acceptance.py`的输入反例确实调用了验证入口，比首批恒真布尔式有进步。
但完整自动合同并未实现：决定分支硬写INCONCLUSIVE，identity为真时reason仍总是POWER；
共同重排只验证输入接受，未比较最终统计；无效draw替换没有实现；模型缺失只是数量检查。
其valid/decision不能作为科学权威，也不应留作后续实验准入工具。

B此前已经从发布完整二类概率独立复算实际50,000 draws及全部统计，实际没有零分母draw，
没有零方差格，数值与风险replicates一致。本次又把官方标签/分组/来源、原模型和输入原件接上。
B手工按冻结顺序裁决实际数据，避免继续消费错误自动token：

- clean upper最大0.3923319<0.5，18个clean head均非恒定。
- 六格Delta为+0.5070、+0.5082、+2.1439、−0.0307、+0.9485、−1.4622pp。
- 六格效应upper均>2pp，不能触发上界KILL。
- 六格冻结功效诊断0.07378–0.58606，均<0.80，故透明重建结果仍不确定。
- ResNet propulsion下界>0；不能说“六格都跨零”，也不能只挑它作为整个研究成功。

保留的历史限制：没有原时点全部内存buffer快照或完整fit命令审计，也不能从现有文件证明
服务器历史上绝无任何未登记test访问。原训练代码/固定架构/eval流程没有提供更新参数的
证据，本轮不补做模型前向去追认过去；这些未知单独披露，不能与假缺失清单混写。
本次不赋予修正数据“重新前瞻确认”的身份。

## 6. 为什么现在结束修复、怎样继续面向顶刊

r014的可恢复身份链和当前数值已查清，继续围绕目录、清单或同一属性扰动重复执行没有新增科学价值。
现有研究贡献仍是方向评价与测量证据；修复成功不会把它升级成TGRS/JPRS创新。

下一步科学问题转为前次全项目重评提出的未成熟候选：
**在相同可见像素、外部训练知识和总资源预算下，显式方向测量相对强旋转不变决策究竟何时有增益，
且这个边界能否在未参与设计的来源上被事前预测？**
它不同于继续证明无增强、狭长规范化分类器怕角度扰动。

科学设计必须先给出真实属性用途/错误代价、一个非事后挑正格的primary endpoint、
完整支持+旋转增强和强不变基线，并排除插值、背景支持及有效像素分辨率的替代解释。
若只能得到又一条预算曲线或小head优势，就不能签作顶刊方案；
若没有可外推、可否证的新预测，则收敛现有测量稿。具体创新论证仍由B负责，
当前不向SERVER发训练或新数据任务，不把资源授权等同于科学假设已成熟。

## 附录：本轮实际只读核查代码

以下均经SSH以已有环境执行，没有写服务器文件。原件日志的选定字段另存上述JSON。
模型读取使用torch.load(weights_only=True, map_location='cpu')，不是模型推理。

### 原模型和日志
```python
import pathlib,json,hashlib,datetime,torch
torch.set_num_threads(1)
r=pathlib.Path('/home/rspip/cqc/study/orientbench')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def when(p):return datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()
pf=json.loads((r/'runs/r013/artifacts/preflight.json').read_text())
g=r/'runs/r012/final_repair_artifacts/primary.json'
t=r/'runs/r012/h1a/canvases/train/manifest.json'
c=r/'runs/r013/calibration/canvases/manifest.json'; cm=json.loads(c.read_text())
model_results=[]
for rec in cm['models']:
 p=r/'runs/r013/models'/rec['name'];ck=torch.load(p,map_location='cpu',weights_only=True)
 log=r/'runs/r013'/rec['name'].replace('.pt','.log')
 entries=[json.loads(x) for x in log.read_text().splitlines() if x.startswith('{')]
 model_results.append({'file':rec['name'],'keys':list(ck),'metadata':{k:v for k,v in ck.items() if k!='state_dict'},'tensor_count':len(ck['state_dict']),'all_tensors_finite':all(torch.isfinite(x).all().item() for x in ck['state_dict'].values()),'matches_original_cal_manifest':sha(p)==rec['sha256'],'epoch_sequence':[x['epoch'] for x in entries],'model_mtime':when(p),'log_mtime':when(log),'log_sha256':sha(log)})
 del ck
print(json.dumps({'preflight_g0_matches':sha(g)==pf['g0_sha256'],'preflight_train_manifest_matches':sha(t)==pf['canvas_manifest_sha256'],'cal_g0_matches':sha(g)==cm['g0_primary_sha256'],'train_rows':len(json.loads(t.read_text())['records']),'cal_rows':len(cm['records']),'cal_manifest_mtime':when(c),'cal_manifest_sha256':sha(c),'models':model_results},indent=2))
for name in ['runs/r013/RUN.json','runs/r014/RUN.json']:
 d=json.loads((r/name).read_text());print(name,'attempts',json.dumps(d.get('attempts'),indent=2))
```

### 原输入清单与缓存
```python
import pathlib,json,hashlib,datetime,numpy as np
r=pathlib.Path('/home/rspip/cqc/study/orientbench');g=json.loads((r/'runs/r012/final_repair_artifacts/primary.json').read_text());pf=json.loads((r/'runs/r013/artifacts/preflight.json').read_text());tm=json.loads((r/'runs/r012/h1a/canvases/train/manifest.json').read_text());cm=json.loads((r/'runs/r013/calibration/canvases/manifest.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
initial=[]
for m,name in zip(g['models'],['resnet50-11ad3fa6.pth','vit_b_16-c867db91.pth']):
 p=pathlib.Path('/home/rspip/cqc/study/pth_data/rareplanes_initialization')/name
 initial.append({'model':m['id'],'matches_g0_initialization_sha256':sha(p)==m['weights_sha256'],'sha256':m['weights_sha256'],'mtime':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat()})
elig=json.loads((r/'runs/r012/final_repair_artifacts/eligible_manifest.json').read_text());E={x['object_id']:x for x in elig}
geo=json.loads(pathlib.Path('/home/rspip/cqc/data/dataset/RarePlanes-Public/real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features']
def inpart(p,part):return any(str(int(p['loc_id'])) in x.split(':')[1].split(',') for x in g['split'][part])
train={i for i,x in enumerate(geo) if inpart(x['properties'],'train') and int(x['properties']['Public_Train'])==1 and i in E}
cal={i for i,x in enumerate(geo) if inpart(x['properties'],'calibration') and i in E}
canvas=[]
for name,root,manifest in [('train','runs/r012/h1a/canvases/train',tm),('old_cal','runs/r013/calibration/canvases',cm)]:
 wrong=[]
 for rec in manifest['records']:
  if sha(r/root/rec['canvas'])!=rec['sha256']:wrong.append(rec['object_id'])
 canvas.append({'partition':name,'rows':len(manifest['records']),'raw_file_sha_mismatches':wrong})
sr=[json.loads(x) for x in (r/'runs/r014/source_audit/source_records.jsonl').read_text().splitlines() if json.loads(x)['partition']=='calibration']
raw=np.load(r/'runs/r014/raw_resnet50_1201.npz') if (r/'runs/r014/raw_resnet50_1201.npz').exists() else None
print(json.dumps({'initialization':initial,'train_set_matches':train=={x['object_id'] for x in tm['records']},'cal_set_matches':cal=={x['object_id'] for x in cm['records']},'train_cal_intersection':len(train&cal),'original_files_vs_recorded_hash':canvas,'original_cal_vs_corrected_objects':{x['object_id'] for x in sr}==cal,'g0_final_matches_preflight':sha(r/'runs/r012/final_repair_artifacts/final.json')==pf['g0_final_sha256']},indent=2))
```

### 官方属性、来源与几何
```python
import pathlib,json,hashlib,csv,numpy as np,tifffile,math
from shapely.geometry import Polygon
r=pathlib.Path('/home/rspip/cqc/study/orientbench');d=pathlib.Path('/home/rspip/cqc/data/dataset/RarePlanes-Public')
g=json.loads((r/'runs/r012/final_repair_artifacts/primary.json').read_text());E={x['object_id']:x for x in json.loads((r/'runs/r012/final_repair_artifacts/eligible_manifest.json').read_text())};geo=json.loads((d/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features'];official={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in csv.DictReader((d/'real/metadata_annotations/RarePlanes_Public_Metadata.csv').open())}
names=[f'{k}_{s}' for k in ('resnet50','vit_b16') for s in (1201,1202,1203)];raw=[np.load(r/f'runs/r014/raw_{n}.npz') for n in names];ids=raw[0]['object_id'];component={int(x):j for j,key in enumerate(sorted(g['split']['calibration'])) for x in key.split(':')[1].split(',')};labels=[];group=[];badsource=[];badgeom=[];headers={};crskeys={}
for oid in ids:
 p=geo[int(oid)]['properties'];e=E[int(oid)];img=official[(int(p['loc_id']),p['cat_id'])]
 labels.append([int(p['wing_type']=='straight'),int(p['num_engines']==2),int(p['propulsion']=='jet')]);group.append(component[int(p['loc_id'])])
 if img!=e['source_cog']:badsource.append(int(oid))
 if img not in headers:
  path=d/'real/imagery/train/PS-RGB_cog'/f'{img}.tif'
  if not path.exists():path=d/'real/imagery/calibration/PS-RGB_cog'/f'{img}.tif'
  with tifffile.TiffFile(path) as t:
   tags=t.pages[0].tags;sc=tags['ModelPixelScaleTag'].value;ti=tags['ModelTiepointTag'].value;keys=tags['GeoKeyDirectoryTag'].value
   headers[img]=(sc,ti);crskeys[img]=list(keys)
 sc,ti=headers[img];pts=[((float(x)-ti[3])/sc[0],(ti[4]-float(y))/sc[1]) for x,y in geo[int(oid)]['geometry']['coordinates'][0]];q=Polygon(pts).minimum_rotated_rectangle;v=list(q.exterior.coords)[:-1];edges=np.diff(np.array(v+[v[0]]),axis=0);length=np.linalg.norm(edges,axis=1);i=int(length.argmax());angle=math.atan2(edges[i,1],edges[i,0])%math.pi
 if max(abs(max(length)-e['L']),abs(min(length)-e['S']),abs(q.centroid.x-e['center'][0]),abs(q.centroid.y-e['center'][1]),abs((angle-e['theta']+math.pi/2)%math.pi-math.pi/2))>1e-8:badgeom.append(int(oid))
geo_codes={}
for image,keys in crskeys.items():
 for i in range(4,len(keys),4):
  if keys[i] in [1024,2048,3072]:geo_codes.setdefault(str((keys[i],keys[i+3])),0);geo_codes[str((keys[i],keys[i+3]))]+=1
print(json.dumps({'all_six_labels_match_official_geojson':all(np.array_equal(z['labels'],labels) for z in raw),'all_six_component_assignment_match_g0':all(np.array_equal(z['component'],group) for z in raw),'source_mismatch_count':len(badsource),'geometry_mismatch_count':len(badgeom),'sources':len(headers),'geotiff_crs_keys':geo_codes,'all_six_object_identity_equal':all(np.array_equal(z['object_id'],ids) for z in raw)},indent=2))
```

### 实际render与独立参考
```python
import ast,pathlib,json,math,numpy as np,torch,torch.nn.functional as F
torch.set_num_threads(1)
r=pathlib.Path('/home/rspip/cqc/study/orientbench')
tree=ast.parse((r/'src/orientbench/r014/evaluate_corrected.py').read_text())
fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='render')
ns={'np':np,'torch':torch,'F':F,'math':math};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'existing_render','exec'),ns);render=ns['render']
E={x['object_id']:x for x in json.loads((r/'runs/r012/final_repair_artifacts/eligible_manifest.json').read_text())}
recs=[json.loads(x) for x in (r/'runs/r014/source_audit/source_records.jsonl').read_text().splitlines() if json.loads(x)['partition']=='calibration'];selected={x['image_id']:x for x in reversed(recs)};rows=[]
for x in selected.values():
 e=E[x['object_id']];rows.append(dict(canvas=str(r/'runs/r014/source_audit/corrected_calibration_canvases'/f"{x['object_id']}.npy"),side=e['canvas_side'],center=e['center'],L=e['L'],S=e['S'],theta=e['theta']))
def ref(q,d,flip):
 c=np.load(q['canvas']);z=q['side']; uv=torch.arange(224,dtype=torch.float64)/224*2-1+1/224;v,u=torch.meshgrid(uv,uv,indexing='ij');t=q['theta']+d+(math.pi if flip else 0);cx=q['center'][0]-int(q['center'][0]-z/2);cy=q['center'][1]-int(q['center'][1]-z/2);px=math.cos(t)*.6*q['L']*u-math.sin(t)*.6*q['S']*v+cx;py=math.sin(t)*.6*q['L']*u+math.cos(t)*.6*q['S']*v+cy;grid=torch.stack([2*(px+.5)/z-1,2*(py+.5)/z-1],-1);return F.grid_sample(torch.from_numpy(c.transpose(2,0,1)).double()[None]/255,grid[None],align_corners=False)
maxref=0.;pair=0.;canon=0.;batch=0.;response=[[],[]]
for q in rows:
 for d in [0.,-math.pi/18,math.pi/18]:
  a=render([q],d,False,device='cpu');b=render([q],d,True,device='cpu')
  maxref=max(maxref,float((a-ref(q,d,False)).abs().max()),float((b-ref(q,d,True)).abs().max()))
  shifted=dict(q,theta=q['theta']+math.pi);pair=max(pair,float((a-render([shifted],d,True,device='cpu')).abs().max()),float((b-render([shifted],d,False,device='cpu')).abs().max()))
  # Equivalent rectangle representation, then explicit long-side RP1 normalization.
  L,S,t=q['S'],q['L'],q['theta']+math.pi/2
  if L<S:L,S,t=S,L,t+math.pi/2
  alt=dict(q,L=L,S=S,theta=t%math.pi);canon=max(canon,float((a-render([alt],d,False,device='cpu')).abs().max()))
  if d!=0:response[int(d>0)].append(float((a-render([q],0.,False,device='cpu')).abs().max()))
for start in range(0,len(rows),16):
 q=rows[start:start+16]
 for d in [0.,-math.pi/18,math.pi/18]:
  joint=render(q,d,False,device='cpu')
  for i,x in enumerate(q):batch=max(batch,float((joint[i:i+1]-render([x],d,False,device='cpu')).abs().max()))
print(json.dumps({'sources':len(rows),'arms':3,'views':2,'max_reference_float64':maxref,'max_theta180_pair':pair,'max_wh90_after_long_side_canonical':canon,'max_mixed_batch_vs_single':batch,'minimum_minus10_pixel_response':min(response[0]),'minimum_plus10_pixel_response':min(response[1]),'model_forward':False},indent=2))
```

