# Research lessons

项目会在新计划、实质修订、上下文变化和 SERVER preflight 前自动做本地避坑检查，无需每轮提醒。普通检查不 fetch、不扫描共享库全文，也不追随远端分支；系统不会自动 fetch。它只使用 `LOCK.yaml` 固定的 SHA，从本地缓存的内容寻址目录 `cache_root/<sha>` 读取紧凑索引，先筛选再加载最多 8 张卡。相同 SHA + context fingerprint 时复用 `APPLIED.yaml`。

`BLOCK` 只表达已验证、无争议且封闭可复现的确定性硬约束；`WARN` 是经验性提醒，可说明理由后继续。`CONTESTED` 不硬拦，`SUPERSEDED` 不应用。共享卡不是科研证据，也不能替代项目内证据审计；详细失败只留在项目。

更新和同步都只能由用户明确触发：只有用户明确说“更新避坑经验”才生成更新预览并允许更新锁；只有明确说“同步避坑经验”才生成提升预览。两条流程的 apply 仍需确认，push 是独立授权；提升流程不 push、不 commit，也不会自动写共享库。

若发布后异常导致安全补偿无法完成，runtime 会把足以恢复的字节保留在 Git 内部的 recovery vault。该记录可恢复工作树，不移动 refs，且不自动删除；其清理由人工审计后另行决定。
