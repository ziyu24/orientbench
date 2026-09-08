# B深度调研证据账（内部来源映射）

范围：截至2026-09-08 UTC可见的遥感多视角、任务可辨识性、遮挡与真值、几何不确定性及实际数据发布。目的是决定下一科学投入，不证明全面查新或录用概率。先读当前main项目教训（基线6b48c67）及本项目证据，再接受历史解释。

## 已完成检索与收敛

第一轮：多视角主动获取/任务效用、off-nadir roof-footprint-height、semantic 3D、物理/参考真值；两条B研究辅助线分别读方法原文和官方资产。第二轮：对每个保留候选检索直接反证，覆盖数据相容区间、visual hull/遮挡、stereo possibility/conformal、RPC bias/gauge。另一次定向追查得到2026-08-30 GeoRay，实质降低“RPC可观测性”新意评价。资产从论文声明推进到官方目录与64字节文件头，不下载大数据。

停止泛搜原因：每个直接方案都有已定位强近邻；剩余缺口是能否提出超过这些近邻的可计算机制、以及真实目标是否可验证。更多同类论文不能替代最小可行性反证。本轮不是系统综述，没有声称穷尽所有2026在线文献。父代理独立核查了MVOI标注原文、Haldar、MVSR3D、GeoRay、stereo区间和WHU两套数据说明。子任务不代表C。

## 关键缺口矩阵

|问题|证据与置信度|矛盾/缺口|决策用途|
|---|---|---|---|
|旧实验是否全无价值|本地原概率复核；高|r020有限阳性与r022候选阴性属不同命题|保留现象，停止候选；不由投入量推断方法价值|
|MVOI是否完整物理足迹GT|原文§3.2；高|明确树遮挡只标可见部分；真实差异发生率未知|不可直接承接完整足迹证明；不能倒推旧阳性伪象|
|几何/双图/不确定性是否空白|下表强近邻；高|部分最新文献仅摘要，不能完整实现对照|排除普通组合包装|
|观测相容目标集合是否新|Haldar/visual hull/stereo区间；高|非线性遮挡处理是否超过既有方法未知|定义集合不是创新；需具体可计算新结构|
|RPC bias与高度分离是否新|传统摄影测量+GeoRay；高|GeoRay预印本代码未验证公开|不能以代码未发否认先验|
|真实外部几何数据可得|WHU-TLC包头实测；高|未下载解包、未看具体成员；DSM非完整足迹|允许制定几何小样本方案，不写数据已在服务器|
|完整足迹独立真值可得|BONAI/US3D等声明；中/低|真实同对象跨视绑定、物理真值与正文尚未一起落实|不派完整足迹确认实验|
|C共识|真实LENOVO审阅单独保存|C本轮执行器故障，独立在线查源受限|只引用真实意见，不说独立复现/共同查新|

## Claim-to-source ledger

检索原生引用只用于内部追踪，交付报告不暴露它们。每行对该来源的报告转述保持简短；论文实验数值除特别注明外没有独立复现。

|ID|作者/来源/时间/URL|实际支持与读取边界|
|---|---|---|
|P01|Weir等，ICCV2019，[SpaceNet MVOI](https://arxiv.org/html/1903.12239v2)|B亲读§3.2：7.8°参考图标注，树遮挡只标可见部分；同城同过境27图。turn69view0。|
|P02|Wang等，TPAMI2022，[LOFT/BONAI](https://arxiv.org/abs/2204.13637)|屋顶mask与roof-to-footprint offset已有方法；B辅助线原文，父首轮见原摘要。|
|P03|Li等，CVPR2024，[MLS-BRN](https://openaccess.thecvf.com/content/CVPR2024/papers/Li_3D_Building_Reconstruction_from_Monocular_Remote_Sensing_Images_with_Multi-level_CVPR_2024_paper.pdf)|多层监督下高度/偏移/足迹联合；辅助线读原PDF。|
|P04|Li等，TGRS2025，[PolyFootNet](https://arxiv.org/html/2408.08645v4)|多输入组合求解、偏移修正；multi-solution不能误读为观测相容集合。辅助线原文。|
|P05|Shao等，Remote Sensing2025，[DualRecon](https://www.mdpi.com/2072-4292/17/23/3793)|作者/出版方摘要明确双图重建改善遮挡与offset。父出版页正文访问失败，不声称审过全部实现。|
|P06|Huang等，TGRS2025-04-23，[MVSR3D](https://skyearth.org/publication/papers/2025_mvsr3d.pdf)|B读作者PDF：SAM/MVS、极线注意力、语义高程交互，DFC19/SpaceNet4。turn75view1。|
|P07|Zhan等，CVPR2024，[Amodal Ground Truth and Completion in the Wild](https://www.robots.ox.ac.uk/~vgg/research/amodal/)|由3D建立amodal真值已有先例；辅助线作者页。|
|P08|Chen等，CVPR2025，[Using Diffusion Priors for Video Amodal Segmentation](https://openaccess.thecvf.com/content/CVPR2025/papers/Chen_Using_Diffusion_Priors_for_Video_Amodal_Segmentation_CVPR_2025_paper.pdf)|视频amodal多合理补全已有先例；样本不是全部可行解的界。辅助线原PDF。|
|P09|Haldar，IEEE TSP2023，[Entrywise Bounds on Nearly Data-Consistent Solutions](https://arxiv.org/html/2212.13614v1)|B原文：已知线性算子下近数据相容集合逐坐标界；不直接覆盖未知遮挡非线性模型。turn69view3。|
|P10|Yao等，ICLR2024，[Multi-View Causal Representation Learning with Partial Observability](https://arxiv.org/abs/2311.04056)|部分可观测多视图可辨识已有理论；具体因果/混合可逆假设不可偷渡。辅助线原文。|
|P11|Wang/Davies，2024，[Perspective-Equivariance for Unsupervised Imaging with Camera Geometry](https://arxiv.org/abs/2403.09327)|相机几何等变重建已有工作；不能把二维透视变换当未知遮挡。辅助线。|
|P12|Guthula等，2026预印本，[Align and Segment](https://arxiv.org/abs/2607.10841)|仿射错位标签对齐学习已有先例；与参考可见截断目标不同。辅助线。|
|P13|Ulman等，2023，[Uncertainty is not sufficient for identifying noisy labels](https://www.frontiersin.org/journals/remote-sensing/articles/10.3389/frsen.2022.1100012/full)|建筑遗漏标签噪声下不确定性识别有限；不能把FCN熵当物理不可见证据。辅助线。|
|P14|Díaz-Más等，Pattern Recognition2010，[Shape from silhouette using Dempster-Shafer theory](https://www.sciencedirect.com/science/article/abs/pii/S0031320310000142)|B出版方摘要：不一致轮廓/遮挡和几何可靠性融合已研究。turn72search0。|
|P15|Tabb，CVPR2013，[Shape from Silhouette Probability Maps](https://openaccess.thecvf.com/content_cvpr_2013/papers/Tabb_Shape_from_Silhouette_2013_CVPR_paper.pdf)|B原PDF可见：概率轮廓、校准误差、pseudo-Boolean优化；不能把概率轮廓交集说新。turn72search14。|
|P16|作者原稿，2024，[Robust Confidence Intervals in Stereo Matching using Possibility Theory](https://arxiv.org/html/2404.06273v1)|B亲读原稿：立体匹配可能性区间及卫星实验已有先例。turn75view0。|
|P17|Dong/Li，Pattern Recognition卷180C刊期2026-12，[Conformalized confidence calibration for multi-view 3D reconstruction](https://www.sciencedirect.com/science/article/pii/S0031320326012148)|B出版方页面已可读，在线日期未核；visibility-aware residual、group calibration、边际覆盖。不能说本日已出版12月刊或已独立验证理论。turn74search0。|
|P18|Dong等，2026-08-30预印本，[GeoRay](https://arxiv.org/html/2608.29680v1)|B亲读全文关键节：RPC ray observability、高度-datum gauge、校准融合和跨来源绝对高程。代码/models will be released；没有复现其数字。turn77view0。|
|P19|Jacobsen，ISPRS Archives2017，[Problems and limitations of satellite image orientation](https://isprs-archives.copernicus.org/articles/XLII-1-W1/257/2017/index.html)|B官方原文摘要：RPC偏差/GCP与高程系统误差早已存在。turn76search0。|
|P20|作者原稿，2021，[Error Propagation in Satellite Multi-image Geometry](https://arxiv.org/abs/2104.04843)|B摘要：全局/局部几何误差分离及LiDAR检验，非本项目发明。turn77view1。|
|A01|武汉大学GPCV，ICCV2021，[WHU-TLC](https://gpcv.whu.edu.cn/data/whu_tlc.html)|B官方页亲读；辅助线2026-09-08 01:58UTC前核open_dataset.rar前64B：HTTP200、RAR5magic、11,163,508,301B。未解包、未核数据许可。|
|A02|武汉大学，JPRS2023，[WHU-OMVS](https://gpcv.whu.edu.cn/data/WHU_OMVS_dataset/WHU_dataset.htm)|B亲读：合成、同基础场景、五同心相机另随航线移动；辅助线readme全文/包头。train.zip实际72,075,168,339B，非页面55.4G。|
|A03|BONAI作者，[发布仓库](https://github.com/jwwangchn/BONAI)|辅助线目录实名trainval/test.zip存在，下载仅病毒扫描提示页；代码MIT非影像许可。|
|A04|GRSS/JHU APL，2019，[US3D/DFC2019](https://www.grss-ieee.org/community/technical-committees/2019-ieee-grss-data-fusion-contest/)|辅助线官方README/torrent元数据200，影像正文未验证；科学匹配不代表资产就绪。|
|A05|作者团队，CVPR2023，[OmniCity](https://city-super.github.io/omnicity/)|辅助线官方链接存在，OpenDataLab未得实际包；视角档不等于独立获取。|
|A06|Liu等，2026-07-10，[ATRNet-LUDO](https://arxiv.org/abs/2607.09078)|作者明确soon available，指定GitHub API404；不能列当前运行资产。|
|A07|GRSS，[DFC2024](https://www.grss-ieee.org/community/technical-committees/2024-ieee-grss-data-fusion-contest/)|官方任务为洪水，不直接验证建筑多视图。辅助线。|
|J01|IEEE GRSS，[TGRS aims and scope](https://www.grss-ieee.org/publications/transactions-on-geoscience-remote-sensing/)|B亲读：新方法与完整实验条件；期刊不按数据集个数自动授予资格。JPRS本轮官方scope403，不假称已查。turn78view1。|

## 未消除的缺口

真实完整地面足迹真值；多个独立城市/过境的同任务实际包；新可计算机制超过强近邻；新方法真实效应。公开页面或文件头可达均不能替代完整解包与输入支持。C离线审阅的事实及结论以原文交付为准。
