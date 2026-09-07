# r016 原生多视角元数据支持核查

执行日期：2026-09-07。执行为 CPU-only；未申请 GPU、未下载或解码影像/标签像素、未读取验证或测试结局、未运行模型或训练。

## 结论

两个资产均为**因信息缺失无法判断**，而不是“无匹配支持”或科学阴性。没有任何已核实的原生三联可支持本轮所需的同一训练地理单位、同传感器/产品、近似成本的近方向与分离方向比较。因此本轮不授权训练或后续自动实验。

## 受控来源与边界

定向查询的新增下载共 141,003 字节（上限 50,000,000）；解包为 0（上限 200,000,000）。逐份来源、哈希和响应保存在 `runs/r016/artifacts/source_manifest.json` 与 `sources/`。固定 dataset 根顶层未发现 SpaceNet/MVOI、US3D 或 DFC 的已登记别名；这不是全盘不存在的断言。

### SpaceNet4 / MVOI

公开 S3 定向列举确认训练入口 `spacenet/SN4_buildings/train/AOI_6_Atlanta/` 下有 27 个候选产品前缀；示例 acquisition 下只有 `MS/`、`PAN/`、`PS-RGBNIR/` 前缀。前缀名作为来源见证已保留，但不是原生 acquisition 身份记录。受限列举没有定位独立 IMD/RPB 或其他原生文本元件，且没有读取影像对象。故 27 个候选在身份、共同训练单位、太阳/时间三步均为 0 通过/0 不通过/27 未知；catalog ID、原生 GSD、时间、太阳/卫星角、RPC坐标系、共同训练地理支持及独立 PSF/MTF/噪声标定均为 unknown。

论文表的目录代理仅作复现：主阈值下 360° 有向代理为 18 个有序三联/10 个首幅，180° 方位轴代理为 0/0；1°/1.05、3°/1.10、5°/1.15 灵敏度分别为 1/0、35/1、43/2 三联。它不证明同地物、同事件、时间/太阳匹配或物理 PSF。`1030010003993E00` 与 `103001000399300` 的 ID 冲突、以及末两 ID 的 GSD/离轴归属冲突仍未由原件消解。

### US3D / DFC2019 Track 3

公开作者 README 确认 Track 3 的命名约定（城市/地理片/原始来源编号）和 RGB 裁片 RPC 已为配准/裁剪调整；它不能提供逐幅原生字段或训练共同覆盖。公开 torrent 仅作为清单读取，列出 `Track3-Metadata.zip` 141,825 字节。官方 DataPort 页面标示 Track 3 Metadata 为 138.5 KB，但要求登录后才暴露文件 URL；依规定没有登录、没有启动 P2P、没有下载或解包该包。因此逐幅 source ID、时间、角度、原生 GSD、IMD/RPB 对应、太阳信息与共同训练单位均未知。

## 可复建

使用已提交的 `configs/r016/metadata_audit.yaml` 和：

```bash
/home/rspip/cqc/data/install/yes/envs/pcp-obb/bin/python \
  src/orientbench/r016/run_metadata_audit.py \
  --dataset-root /home/rspip/cqc/data/dataset --out runs/r016/artifacts \
  --table doc/MVOI_TABLE8_TRANSCRIPTION_20260906.csv --config configs/r016/protocol.json
```

正式运行登记在 `runs/r016/RUN.json`，状态 `COMPLETE`。完整结果包括原生字段规范、冲突表、逐步计数、完整（空）已核实三联清单及公开表代理结果，全部位于 `runs/r016/artifacts/`。
