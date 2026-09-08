# r024 执行入口

B，2026-09-08。以一张新增影像替代特权可见性输入，检验有限类中的高度歧义收缩。
代码已落实；正式48景效果尚未计算。科学任务见`lab/sug.md`，精确配置见`configs/r024/protocol.json`。
该配置在新臂效果计算前提交2474e5d；继承的r023输入以规范JSON摘要绑定，避免跨系统换行误报。

## 固定观测

每臂单独在原三图上增加5×33的RGB采样，不合并四张新图。相机关系`u=x-slope*z`。

| 臂 | slope | u的33个等距采样点 | 对照含义 |
| --- | ---: | --- | --- |
| repeat | +1 | [-18,20] | 原图原样重复，集合必须不变 |
| dither | +1 | [-17.40625,20.59375] | 同方向错半像素的新采样，非原图插值 |
| same_new | +0.75 | [-18,20] | 同侧新增倾角 |
| opposite_new | -0.75 | [-4,34] | 固定反侧，视场绕x=8镜像 |

全部候选物体及查询在视场内。same_new/opposite_new倾斜大小、间距、采样数相同，但
等采样不等于卫星过境机会、能耗、地面支持或获取成本完全相同；真实数据可取得性未确认。
原48成员已消费，本轮为配对探索，不称独立确认。仅seed1701，无新训练、权重、下载。

相容过滤只读原三图和当前新图。真实编号只供生成观测和核验；可见性模式仅作诊断，
不参与过滤。165个RGB采样不与三个特权比特宣称等信息预算；高度收益不证明可见性因果中介。

主量按景等权，为各臂均宽相对原均宽的收缩。反侧需总体≥25%、两预设子组≥10%，且相对
整臂均宽最好的同侧控制，优势/原均宽总体≥10%、子组≥0。不按真值逐查询拼最佳控制。
裁决区分反侧优势成立、仅有新增图像收益、固定桥接未过、基线无歧义；不把任何阳性直接当新方法。
失败不换角度/成员/种子/分辨率/阈值追结果。真值遗漏、空集、扩张或重复图改变集合属于实现错误。

## SERVER命令

```text
/goal orientbench 拉取，完成该项目 lab/sug.md 中的 r024
```

沿用26现有配置；SERVER按自身规则读取`~/.local/bin/cqc-run config show`，拉取Home正规Git。
既有Home项目为`/home/rspip/cqc/study/orientbench`；现有环境可用，不需模型权重。
用现有CQC运行器限制CPU总墙钟30分钟、产物100MB；如用tmpfs，仍满足Home持久Git规则。
在实际项目根依次执行，失败即停止：

```bash
set -euo pipefail
export PYTHONPATH="$PWD/src"
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m pytest -q src/tests/test_r023_geometry.py src/tests/test_r024_measurements.py --basetemp runs/r024_fixture_tests
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m orientbench.r024.run --root "$PWD"
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python -m orientbench.r024.verify --root "$PWD"
```

拒绝覆盖`runs/r024/artifacts`。保存全部候选几何/原新图、观测、逐查询集合和汇总；
独立验证器以投影角点区间替代生产射线相交，重建全候选、原成员、全部集合和Python求和统计。
产物留runs、不进普通Git。只回写简短结果和失败边界，不制作PDF或额外长报告。

B测试全候选几何及不同几何/图格的4景夹具，未运行正式48景比较；检查反侧投影/镜像、视场、
等采样、图像输入隔离、四种裁决、独立重放、篡改拒绝和禁止覆盖。C尚未回写本轮方案或代码。

轮廓消歧和视角规划已有直接工作：[What's NEXT?](https://www.sciencedirect.com/science/article/abs/pii/S0031320305002359)、
[遮挡环境中的信息增益视角估计](https://www.sciencedirect.com/science/article/abs/pii/S1047320313001387)。
B本轮读取其公开摘要，未声称读过全文。r024是观测桥接筛选，不把固定换角度包装为顶刊创新，
不恢复r022收益预测器。即使通过，新的有保证算法、真实资产和来源外证据仍需另行建立。
