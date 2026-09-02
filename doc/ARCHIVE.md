# 历史归档与恢复

极简改造的直接父提交是：

```text
09381f7a360e5ad730e77157fb427401555620f5
```

该提交保存改造前3278个跟踪文件、全部旧实验代码、协调记录和Git内证据。r002执行证据ref为：

```text
exec/r002-evidence-closeout-repair-final
8236d149b02268135485f1076bb6c0fdd3c74a55
```

查看单个旧文件：

```bash
git show 09381f7a360e5ad730e77157fb427401555620f5:<path>
```

建立只读历史工作树：

```bash
git worktree add --detach ../orientbench-history 09381f7a360e5ad730e77157fb427401555620f5
```

本次没有改写Git历史、删除远端历史ref，也没有删除服务器run回执、数据、权重或大型产物。
旧内容需要复核时从上述提交读取，不把旧控制面重新复制到当前主线。

