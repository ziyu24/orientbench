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

## r026更正执行入口（B，2026-09-08）

B未修改服务器工作树或原r025产物。修正模块仍在`src/orientbench/r025/`，不复制第二套框架；
新配置是`configs/r026/protocol.json`。运行和验证模块均支持`--run-id r026`，输出到
`runs/r026/artifacts/`，不会覆盖`runs/r025/artifacts/`。使用主机既有Python环境及
`PYTHONPATH=src`运行`orientbench.r025.run`、`orientbench.r025.verify`；8项纯内存测试是
`orientbench.r025.test_pairing`。STRtree查询按Shapely 2接口，现有执行环境已核实为2.1.2。

`b_review.py`独立从原生标签重建对应与候选边，B已通过标准输入在服务器内存运行，没有
服务器文件写入；全458对比较零差异，原件摘要和细节见`R025_B_REVIEW_20260908.json`。
原核验器仍保留图像解码核查，现额外要求原生对应重放和逐对象唯一引用，不能再用覆盖集合
替代语义验证。原图原生坐标在本次范围满足1e-6格点核查；不外推为任意浮点坐标容差算法。

现有`run.py`的预测元数据输出仍只是登记位置初查，**不是r026完整来源调查入口**。
SERVER须在本项目内补足定向查找与实际生成配置核验并保存逐项证据；可以扩展此模块或添加
同目录小模块，禁止仅调用旧初查然后宣称调查完成。优先查上文登记的历史生成程序与归档
清单，实际Home/tmpfs位置按主机配置确认。通用目录查询继续遵守上面的当前main/发布副本规则。
