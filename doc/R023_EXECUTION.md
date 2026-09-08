# r023 服务器执行说明

本任务已于2026-09-08完成并由B复算；下方命令仅为历史重建入口，当前活动任务以`lab/sug.md`为准。

B；本轮只交付代码、配置和简短任务单，不制作PDF。

## 科学合同

- 3,125候选：五个固定位置的不透明柱体，高度各取0/2/4/6/8；0表示地面。
  地面和物体分别固定RGB，物体同色、无光照/纹理/噪声。三台正交相机同方位，
  水平/垂直方向比0.5/1/2；每图5×33采样。所有坐标和边界规则见固定配置。
  这是有限几何类的轮廓实验，不是纹理匹配、真实卫星、RPC或完整足迹验证。
- 每个候选用自身最高表面计算四个固定查询的可见性，所有候选高度均在视场内。
  正射线距离处闭柱体相切算遮挡；地面向上无遮挡，自身最高表面不遮挡自己。
- 48真场景按seed1701的SHA256排序从四个几何池各取12，已生成固定清单。
  中心查询全可见且高程<4为unoccluded，全可见且高程>=4为depth_boundary；
  后者具有固定近边缘查询和相邻地面查询。部分可见为one_side_occluded，全不可见为common_occluded。
  池大小200/750/750/1425。这是刻意平衡、与高程相关的合成分层，不是自然发生率或独立遮挡因果干预。
  选取不用影像相容性、区间宽度或效果；推断不用组别、真场景编号或真实高度缩小候选库。
- 强基线对全部3,125候选按完整三图逐字节匹配，求目标高程精确最小/最大值。
  oracle每次只多给当前查询3个可见性比特，不合并四查询、不提供对应点或深度。
- 192查询全部保留，先景内等权再景间等权；主量为两个均宽之比的收缩率。
  总体>=25%，部分遮挡/深度边界各>=10%才支持该有限特权信息筛选。
  分母0记null及无空间；不删零宽/000、不加epsilon、不改阈值或种子。
  零遗漏、零空集、区间不增属于实现条件。结果不证明RGB可推断oracle，不自动训练。

配置：`configs/r023/protocol.json`；48场景：`configs/r023/manifest.json`。
B在正式效果计算前提交这两份文件。B只做几何核对和另一套四场景小夹具，未计算正式48景效果。

## SERVER入口

```text
/goal orientbench 拉取，完成该项目 lab/sug.md 中的 r023
```

26配置已只读核对：Home项目`/home/rspip/cqc/study/orientbench`，已有
`/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python`可用，NumPy1.26.4。
按已有SERVER规则拉取Home Git并用现有CQC运行器记录本轮；使用tmpfs时满足Home持久Git规则。
本轮无需模型、数据包或新环境，B不远程启动实验。

在实际项目运行根依次执行，现有运行器设总墙钟30分钟，产物上限100MB，CPU执行：

```bash
set -euo pipefail
export PYTHONPATH="$PWD/src"
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m pytest -q src/tests/test_r023_geometry.py --basetemp runs/r023_fixture_tests
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m orientbench.r023.run --root "$PWD"
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m orientbench.r023.verify --root "$PWD"
```

前一步失败就停，不能用后一步退出码覆盖失败。应用拒绝覆盖既有`runs/r023/artifacts`；
若已存在先只读查明，不清空原件重跑。

`run`保存全部候选参数/影像/查询几何、48份观测、192行及全部相容ID；`verify`
不调用生产几何/统计函数，改用投影包络与解析阴影重算全部候选，重建集合和统计。
两种实现只验证同一有限合同，不代表真实成像模型已验证。

完成后只将简短数值、边界和产物入口写入结果账；有有效负结果再写失败账。
产物留runs、不进普通Git。报告总体/四类均宽、收缩、零宽/全范围计数、独立复算和资源。
枚举/验证失败时不得写科学成败。不生成PDF，不改r020/r022结论，不自动追加实验。

## 本地验证

7项测试通过：全候选双算法几何一致、已知遮挡反例、几何独立选样、视场越界拒绝、
oracle查询隔离、均值比/零分母、小型独立夹具全流程/拒绝覆盖/篡改证据拒绝。
小夹具使用不同柱体位置、高度、图格和4场景，不是正式48场景的试跑或调参。
