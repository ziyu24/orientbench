# orientbench

[人类入口](docs/HUMAN_GUIDE.md)

项目功能、当前配置和受控设置入口由Codex运行 `python -m tools.workflow help --section all` 查询；用户无需手工编辑配置。项目默认 `UNLOCKED`，锁状态见 `.research_core/PROJECT_LOCK.yaml`；切换后由Codex提交到`main`，各端fast-forward核验后跨端生效。

本项目固定使用内容寻址的 research lessons；规则、显式更新/同步口令与恢复边界见 `coordination/lessons/README.md`。
