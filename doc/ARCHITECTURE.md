# 架构

项目只有一个 Python 包 `src/orientbench/`。`core` 保存几何与常量，`data` 负责数据语义，
`io` 负责输入输出，`metrics` 保存纯指标，`probes` 组合最小科学探针，`reports` 只生成报告，
`runners` 负责受控调用。依赖方向保持由组合层指向基础层，不引入第二套运行框架。

测试与源码同处 `src/`，由根目录 `pyproject.toml` 统一发现。未来实验代码也进入 `src/`，
配置进入 `configs/`；不得在项目根重新创建 `scripts/`、`tools/`、`experiments/` 或协调树。

科学交互只经过 `lab/` 四文件。SERVER运行时选择Home或精确shm项目根，产物进入该项目的
`runs/<rNNN>/`；项目Git只保存代码、配置和结论。

