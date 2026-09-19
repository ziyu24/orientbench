# r029：固定标签下完整 AP 差的抽样可行性

本轮是点估计基线实验，不是新算法、有效置信区间或顶刊贡献的验收。目标量是固定453图上
Rotated RTMDet-M减Oriented R-CNN的AP；AP50为主，AP75只作辅助。原clean预测在交付期间
被另一项已授权历史清理删除；先用固定权重/配置每模型各以2卡恢复一次全453图预测，再
进行CPU抽样。不训练、不人工标注。HRSC已被项目使用，属于开发模拟，不是新留出验证。

## 科学实现

1. 总体及顺序来自冻结的official test清单，不从预测反推。核查trainval/test数量、重复、
   交叉及加载覆盖，逐框比较原生XML经标准HRSC加载器转换后的GT与两套缓存，核对实际图像
   路径和尺寸。配置绑定清单、XML清单和两模型权重/基础配置摘要；旧预测摘要保留为历史
   对照。恢复产物另记摘要，不要求pickle逐位相同；不搜索替代输入。
2. 标准匹配直接复用MMRotate，独立r028追踪恢复到原预测索引后逐项核对TP/FP。全局排序使用
   原float32预测、test清单顺序及当前标准程序的np.argsort；它不承诺稳定同分排序。完整前缀
   recall/precision与未修改评价器必须逐项相等。加权估计使用float64，全查AP差异容限1e-7。
   记录NumPy版本及评价源码摘要。当前HRSC加载器不依据XML difficult设置ignore，保留此
   既有口径并报告XML difficult与实际ignore计数，不称其已经复现所有HRSC评价实现。
3. 固定整图预算48/96/192/384/453，两模型共用被查图；每种预算500次设计重复，单个
   PCG64(29029)随机流。每次重复生成整图排列，各预算嵌套，算法不依据中途结果停。
   这些是抽样误差模拟，既没有训练种子，也不代表500个独立数据集。
4. SRS为整图简单随机无放回抽样，权重N/n。预测分层只用两模型score>=0.3预测数之和，
   数量降序、同值按数值image ID；前ceil(N/4)为高层。高层取min(N高,floor(n/2))，
   其余预算给低层，各层无放回，HT权重N层/n层。高层饱和后完整查询该层。第三臂查询同一
   分层集合，但全部权重设1，作为忽略抽样设计的消融，不包装成另一种主动方法。
5. 每图oracle返回每个模型完整图内匹配产生的全局位置、TP、FP、有效GT数；估计器只接收
   已查图向量，以相同权重估计所有前缀TP/FP及GT总数，再计算VOC07十一点插值。未查图的
   GT数/匹配信息、旧24图的GT密度以及全量AP不进入选样或估计器。全标签在评估驱动中缓存
   只为加速模拟；查询计划先保存，之后才计算全量AP。此接口隔离是防泄漏措施，不是安全沙箱。
6. HT累计量的设计无偏性不使AP无偏。均匀权重在AP比率中消去；SRS的HT代入与继承全局
   同分顺序的子集AP是同一个估计，不能算两臂进步。不重新对子集同分项排序。无有效GT样本
   的估计按0记录并计数，不能丢弃。不使用已查图最大GT数作总体上界。

报告有符号偏差、RMSE、MAE、90%绝对误差分位数、误差<=0.01的频率及零GT次数，单位为
AP的0—1量纲，0.01即1个百分点。只有全量差绝对值>=0.01时才报符号错误率，否则标记
“不作有实用差异的胜负判断”。另外报告分层相对随机的配对MSE差、Monte Carlo标准误及
RMSE比；Monte Carlo精度不是一次标签查询所得AP差的置信保证。全查预算用于正确性检查。

本轮不产生AP置信区间，故不存在可报告的95%区间覆盖率或随时停止结论；也不拿500次
模拟误差分位数当实际查询时可用的区间。有限总体点估计是否值得继续，是先于有效区间
构造的一个问题。如果随机抽48/96图已经很准，应如实记录新方法空间有限；如果分层更差，
只否定本次预测计数分层的收益，不否定所有主动查询。如果两者都不准，报告当前困难，
不能改预算、分层变量或阈值追结果。该阶段没有期刊升级成功门。

[Active Testing](https://arxiv.org/html/1807.00493v1)已研究少查询下AP估计；
[Active Model Selection](https://link.springer.com/article/10.1007/s10994-024-06603-1)
研究模型选择的方差最小化。当前分层基线不是这两项工作的复现/合理完整适配。本轮只完成
最小可行性基线；提出方法优势前仍必须补齐相应对照和合法区间推导，不能凭胜过随机称新颖。

## SERVER入口（沿用26）

从主机配置取dataset、项目Home、tmpfs和环境根；旧`runs/r004`已于2026-09-19 13:46 UTC
被授权清理（8a99f2c）。本任务仅恢复两模型clean预测至当前实际项目运行根
`runs/r029/inference/test`，不恢复历史干预图、训练或其他轮次；抽样输出为`runs/r029/artifacts`。
沿用含MMRotate/MMCV的pcp-obb环境，不创建环境或下载模型。依既有cqc-run执行方式脱离
SSH执行。私库索引最新main匿名访问404，B已定向核对服务器发布副本及原权重/配置实体
摘要，二者与旧来源一致；不宣称拿到了最新main。下面路径是26当前可用的具体入口。
SERVER分配两个可用GPU，使每次torchrun的两个rank实际分担本模型图像，不以两个模型各
跑一卡替代。保持原配置每卡test batch和处理规则；分布式补齐由原生收集器处理，最终
预测必须恰为453个唯一ID，否则报错。记录实际启动命令及两rank进程/GPU证据。

```bash
export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1
PY=/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python
TOOL=/home/rspip/cqc/data/install/yes/envs/pcp-obb/lib/python3.10/site-packages/mmrotate/.mim/tools/test.py
"$PY" -m unittest discover -s src/tests -p test_r029_sampling.py
"$PY" -m orientbench.r029.verify
"$PY" -m orientbench.r029.recover \
  --config configs/r029/protocol.json \
  --dataset /home/rspip/cqc/data/dataset/HRSC2016 \
  --pth-root /home/rspip/cqc/study/pth_data --run-root runs/r029

# SERVER先按现行规则选定两个GPU；两项依次执行，已有完整合法输出则复用。
"$PY" -m torch.distributed.run --standalone --nproc_per_node=2 "$TOOL" \
  runs/r029/inference/test/rotated_rtmdet_m/clean/runtime_config.py \
  /home/rspip/cqc/study/pth_data/baseline_rotated_rtmdet_m_fpn_9x_le90/HRSC_trainval_test/best_mAP_9065_epoch_32.pth \
  --launcher pytorch --out runs/r029/inference/test/rotated_rtmdet_m/clean/predictions.pkl
"$PY" -m torch.distributed.run --standalone --nproc_per_node=2 "$TOOL" \
  runs/r029/inference/test/oriented_rcnn_r50/clean/runtime_config.py \
  /home/rspip/cqc/study/pth_data/baseline_oriented_rcnn_r50_fpn_3x_le90/HRSC_trainval_test/best_dota_mAP_epoch_34.pth \
  --launcher pytorch --out runs/r029/inference/test/oriented_rcnn_r50/clean/predictions.pkl
"$PY" -m orientbench.r029.run \
  --config configs/r029/protocol.json \
  --dataset /home/rspip/cqc/data/dataset/HRSC2016 \
  --predictions runs/r029/inference/test --rebuilt --output runs/r029/artifacts
```

SERVER先复用B有效检查，只补实际入口、两卡首批及吞吐；通过后直接完成两模型恢复和固定
500次抽样。若输入变化或前缀不一致，保留具体差集/错误，修复同任务的工程问题；不换模型
或自动另开研究任务。标准test顺带输出的全量AP不可用于改抽样设计或checkpoint选优。
summary、输入绑定及检查结论入现有结果账并提交推送；原始预测和逐次
查询/估计留runs，不入普通Git。不删除r028原证据，不修复或交付已取消的盲标包。

产物：恢复预测及来源、native_input_audit.json、input_audit.json、query_plans.jsonl、
replay_checks.json、estimates.jsonl、summary.json。保存Home Git中的恢复入口和结果摘要后
推送，大产物留执行端；当前任务依赖的两套预测不得再按旧r004清理清单处理。
