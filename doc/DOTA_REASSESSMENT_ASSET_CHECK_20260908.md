# DOTA重评的定向资产核验

B于2026-09-08 06:47:29—06:50:57 UTC通过既有SSH只读核验26；未修改服务器、拉取代码、
加载模型或启动实验，未读取官方隐藏test。先读cqc-run配置并核对仓库为
`https://github.com/ziyu24/orientbench.git`，Home与实际runs均在
`/home/rspip/cqc/study/orientbench`，服务器HEAD为`ee959ed`。

数据根为`/home/rspip/cqc/data/dataset/dota`。DOTA1.0/1.5验证标注各458文件，DOTA2.0验证
标注593文件。`src_image_dota10_dota15/val`与`src_image_dota20/val`同名PNG交集458张；
只对词序最先3张做了全文件SHA-256核对，均相同，未宣称其余455张已验证。

|文件|两个版本共同的SHA-256|
|---|---|
|P0003.png|3967fbaf9671f642030ac5d858fb9637e68859aed0e1ba5cfc72538656251d8d|
|P0004.png|525e22bb609633ecd4bab8434f0c64ff1538d975fdac9f6d23f8b77e8c108d78|
|P0007.png|0821677ab2be8f0fa44133cec37cb99f123e4f8f7af264258e1b230dcdbb21dd|

历史Git原件`09381f7a360e5ad730e77157fb427401555620f5:reports/069_dota_clean_artifact_manifest.csv`
登记ORCNN/RTMDet的AP50为.7061/.7161，评价是5,297切片、55,804 GT。逐实例JSONL为
matched-only，不能据此重算新标签下完整AP，也不能将此切片分数称458母图合并后的官方分数。

同一历史提交中`top_journal_v3_reaudit_055/dota_external_replication_r025_20260813/run_r025.py`
使用完整预测`outputs/persistent_artifacts/orientbench_r019/prelabel/raw/{orcnn,rtmdet}/identity.pkl`
及`tile_to_mother.csv`。本轮在26 Home项目的这两个精确路径未找到文件，映射与registry的
同级登记路径也未找到。只能说明登记位置缺失，不能说全项目/其他存储中无法恢复。
未继续全盘搜索，未打开其他项目；未为了填补缺口把匹配记录当成完整预测。

当前准备程度：同像素配对具有实际入口，完整458图哈希、版本发布身份、标签差异、完整
预测所在位置/分数截断/切片合并、模型训练接触与映射尚未核实。本轮没有新的AP比较结果。

## r025执行定位补充（B，待SERVER执行，不是新结果）

科学范围与唯一任务见`lab/sug.md`。SERVER先按本机`cqc-run config show`解析当前固定目录并
核对仓库身份；以上路径只是上次观察，不能覆盖主机配置。定向检索本项目正规Home、实际
运行根及其已登记归档；不全盘遍历、不进入其他项目，也不运行旧审批/锁脚本。

实现放`src/orientbench/r025/`，参数放`configs/`；运行明细放`runs/r025/`。
当前源码`data/dota.py`与`data/gt_index.py`含旧DOTA解析/切片约定，须核对后再复用；本轮
输入是原图原生多边形，不能直接沿用只支持旧split的索引。旧`runners/inference_runner.py`
保留历史控制代码，不作为本轮入口，也不为这次任务恢复它。

最小输出为`image_pairs.csv`、`label_correspondence.csv`、`label_summary.json`、
`prediction_sources.json`及简短结果Markdown；多义候选边可用单独压缩表保存。
表需含来源文件/原行号/版本、输入摘要、逐图尺寸及像素一致性、计数分母和明确未知项；
具体路径、摘要、模型配置及实际搜索范围记录在运行清单中，不塞进科学任务单。

若需核对通用模型重建入口，先查询`ziyu24/cqc_pth_data`当前main的`README.md`主机入口与
`doc/catalog.md`中ORCNN/RTMDet和DOTA相关行；读取失败如实记录，可查配置中`pth_data/readme.md`
发布副本。仅查元数据，本轮不下载或加载权重。服务器应完成源码、配置、小型结论的Git
提交推送；tmpfs执行时恢复所需小文件也必须进入Home持久主仓库历史。
