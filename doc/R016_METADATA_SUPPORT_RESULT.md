# r016 原生多视角元数据支持核查

**B 复核说明（2026-09-07 UTC）：接受信息不足的结论，本轮实际只完成受限公开入口检查，
未能实施原生三联匹配。直接原件核对与结束决定见 `doc/R016_B_REVIEW_20260907.md`。**

执行日期：2026-09-07。执行为 CPU-only；未申请 GPU、未下载或解码影像/标签像素、未读取验证或测试结局、未运行模型或训练。

## 结论

两个资产均为**因信息缺失无法判断**，而不是“无匹配支持”或科学阴性。没有任何已核实的原生三联可支持本轮所需的同一训练地理单位、同传感器/产品、近似成本的近方向与分离方向比较。因此本轮不授权训练或后续自动实验。

## 受控来源与边界

末次保留的七份响应体共 141,003 字节（本轮下载上限 50,000,000）；解包为 0。B 已逐份核实长度和哈希，但计数在每次调用时重置，故历次尝试的累计网络流量未被完整审计。逐份来源、哈希和响应保存在 `runs/r016/artifacts/source_manifest.json` 与 `sources/`。固定 dataset 根顶层未发现 SpaceNet/MVOI、US3D 或 DFC 的同名入口；这不是对所有已登记别名或全盘不存在的断言。

### SpaceNet4 / MVOI

公开 S3 定向列举确认训练入口 `spacenet/SN4_buildings/train/AOI_6_Atlanta/` 下有 27 个候选产品前缀和一个 `geojson_buildings/` 前缀；仅进一步列举了一个产品目录，其下有 `MS/`、`PAN/`、`PS-RGBNIR/`。前缀名是目录见证，不是原生 acquisition 身份记录。此次没有取得独立 IMD/RPB、训练成员或边界文本，没有穷尽其他产品和子目录，不能断言原生文本不存在。原输出三步的“0/0/27”以产品目录为单位，不能解释为三联筛查；原生共同支持三联的总体和合格/不合格数量均未知。原生 ID 归属、GSD、时间、太阳/卫星角、RPC坐标系及独立 PSF/MTF/噪声标定也均未核实。

论文表的目录代理仅作复现：主阈值下 360° 有向代理为 18 个有序三联/10 个首幅，180° 方位轴代理为 0/0；1°/1.05、3°/1.10、5°/1.15 灵敏度分别为 1/0、35/1、43/2 三联。它不证明同地物、同事件、时间/太阳匹配或物理 PSF。`1030010003993E00` 与 `103001000399300` 的 ID 冲突、以及末两 ID 的 GSD/离轴归属冲突仍未由原件消解。

### US3D / DFC2019 Track 3

公开作者 README 确认 Track 3 的命名约定（城市/地理片/原始来源编号）和 RGB 裁片 RPC 已为配准/裁剪调整；它不能提供逐幅原生字段或训练共同覆盖。公开 torrent 仅作为清单读取，列出 `Track3-Metadata.zip` 141,825 字节。官方 DataPort 页面标示 Track 3 Metadata 为 138.5 KB，匿名响应中该条目只有访问弹窗，没有文件下载 URL；页面的开放数据登录说明与通用订阅弹窗并存，登录后的可取得性和费用均未验证。本轮没有登录、启动 P2P、下载或解包该包。因此逐幅 source ID、时间、角度、原生 GSD、IMD/RPB 对应、太阳信息与共同训练单位均未知。

## 可复建

使用已提交的 `configs/r016/metadata_audit.yaml` 和：

```bash
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python \
  src/orientbench/r016/run_metadata_audit.py \
  --dataset-root /home/rspip/cqc/data/dataset --out runs/r016/artifacts \
  --table doc/MVOI_TABLE8_TRANSCRIPTION_20260906.csv --config configs/r016/protocol.json
```

运行登记在 `runs/r016/RUN.json`，状态 `COMPLETE`。保存的是缺失字段说明、待解冲突、目录单位的未知计数、空的已核实记录清单及公开表代理结果，位于 `runs/r016/artifacts/`；这不是已经完成原生匹配实验的证明。r016 经 B 复核后结束，当前无活动任务。
