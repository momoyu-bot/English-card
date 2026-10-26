# git

机房手册的一本，目录在 [`tools/README.md`](../README.md)。

- `tools/` 的检查脚本都已带上 `-c core.quotepath=false`。
- main 2026-09-27 改写过历史：旧克隆推之前先 `git -c core.quotepath=false fetch origin main` 再 `git -c core.quotepath=false rebase origin/main`；别 merge 旧的 main、别强推、
  别合并 `backup/before-momo-fix-2026-09-27`。
- 2026-09-27 改写历史，是为了把一笔署成那个错邮箱的提交改回她的号；merge 一次旧的 main，那张陌生的脸就回来了。
  推完可以看一眼 `https://api.github.com/repos/momoyu-bot/English-card/contributors`，应该只有 momoyu-bot、github-actions[bot]、claude。
- 本仓库的开工入口：cc 在云端读 `CLAUDE.md`，有它就不读 `AGENTS.md`；build 同目录两份都读；Codex 只自动读 `AGENTS.md`；反重力读 `AGENTS.md` 和 `GEMINI.md`。两家未见 CLAUDE.md 正文就按 AGENTS.md 打开全文；已经完整加载的不重复读。
- 云端不能依赖这台电脑的全局文件；共用底线放仓库，本地入口只留跨项目偏好、机器配置和不能公开的技术信息。
- 拆到 `.claude/rules/` 也不能保证给 build 减量，它兼容读取那里；不为瘦身自动导入全部手册。
- cc 的技能通常先挂名字和简介、用到才读正文；build 兼容 Claude 的技能，但不把两家的具体加载策略当成完全相同。要改自动加载方式，先核当前实现。
- 仓库 PR 权限是「有写权限的人才能提」。开 PR 报错先看是不是 PR 功能被整个关了。
