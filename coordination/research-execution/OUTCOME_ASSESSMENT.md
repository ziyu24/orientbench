# SERVER 完成后的 B/C 科研评估

SERVER 的 `COMPLETE` 只证明命令、机器验收、非空结果和远端提交一致，不允许 SERVER
自行评定刊会等级。B、C 或用户显式启用的 DOCTORAL 读取计划绑定的已核验结果提交后使用
`execution scientific-assess --request build/research-outcome-assessment.yaml` 记录评估。

请求必须区分已确认事实、合理推测、个人观点和暂不可验证信息，先指出错误前提或信息
缺口；若不同意当前判断，写明理由、反例或风险。科研评级固定注明中科院 2025 最终版、
当前等级必须用`benchmark_zone`精确选择“一区”“二区”“三区”或“四区”，同时从
`research/venue-benchmarks/CAS-2025-FINAL.yaml`选择同区具体期刊；运行时自动附加地球科学
大类口径、来源与核验日期，相关小类只作事实说明。参考期刊必须出现在至少一篇含题名、期刊、
年份、DOI 或 URL 的对标论文中。不得用自由文字替代分区。三区或四区、以及任何低于 TGRS 的
结果，其唯一合法科研动作是继续下一 `rNNN`；达到门槛只能记为
`GOAL_REACHED_CANDIDATE`，不是投稿或录用保证。

用户可见回复保持四项：结论、关键证据、刊会差距、唯一下一步。状态确认和角色确认不
重复做期刊评级。当前模型无法可信解决关键创新判断时，必须建议更高模型并说明收益与
token 代价。
