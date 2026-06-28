# point2rbox Download 025

> 2026-06-28 12:04:12 CST

- target: ted.pth (TED edge model for generator init)
- url: https://www.modelscope.cn/models/wokaikaixinxin/mmrotate/resolve/master/Point2Rbox_v2/ted.pth
- modelscope SDK model_file_download → repo 404；direct resolve → JSON "获取模型文件失败，文件内容为空" (Code 10990101007)。
- 结论: **upstream 文件服务器端为空/不可用**（非 auth 问题）→ status=blocked_download_source_empty。
- point2rbox **weak_nonformal**，不进入 formal gate。若需: 寻找其它镜像/官方 release 的 ted.pth。

---
## 026 update (2026-06-28 12:28:44 CST)
- 续找 ted.pth: github(yuyi1005/point2rbox-mmrotate releases)→9字节(asset 不存在); huggingface(wokaikaixinxin)→401; modelscope→文件内容为空。
- 结论: **blocked_upstream_artifact_unavailable**（所有上游源不可用）。point2rbox 保持 weak_nonformal，不进 formal gate。
