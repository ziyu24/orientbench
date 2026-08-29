# 项目运行目录

常规可提交结果位于项目 `runs/<instruction-id>/`，其中 `<instruction-id>` 是从 `r001` 起的项目级 `rNNN` 编号；目录继续使用 `source/`、`config/`、`logs/`、`checkpoints/`、`outputs/`、`tmp/` 六个子目录。训练数据、缓存和大型中间制品不得放在这里，而应通过集中 manifest 展开到 `/dev/shm` 项目镜像中的 `large-workspaces/<profile>/`。

运行内容默认不进入 Git；小型正式回执写入 `coordination/executions/`，大制品恢复信息集中写入 `artifacts/manifests/`。禁止在项目外、项目根目录或同级目录随手建立实验目录。
