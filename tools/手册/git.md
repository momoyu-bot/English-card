# git

机房手册的一本，目录在 [`tools/README.md`](../README.md)。

- `tools/` 的检查脚本都已带上 `-c core.quotepath=false`。
- 2026-09-27 改写历史，是为了把一笔署成那个错邮箱的提交改回她的号；merge 一次旧的 main，那张陌生的脸就回来了。
  推完可以看一眼 `https://api.github.com/repos/momoyu-bot/English-card/contributors`，应该只有 momoyu-bot、github-actions[bot]、claude。
- 谁自动读哪份（2026-09-28 对过两家官方文档）：Grok Build 读 `AGENTS.md` 和 `CLAUDE.md`，为了兼容也读 `.claude/rules/` 里的 `.md`
  （docs.x.ai/build/features/project-rules，没提按路径挑着读）；cc 在仓库里有 `CLAUDE.md` 时只读它，不读 `AGENTS.md`
  （code.claude.com/docs/en/memory 的 AGENTS.md 一节）。机房手册（`tools/README.md` 和 `tools/手册/`）谁都不自动读。
  所以把 `CLAUDE.md` 拆进 `.claude/rules/` 减不了 Grok 的体重，只是多出一本笔记。
  技能（`.claude/skills/`）在 cc 那边平时只挂名字和简介、用到才拉正文；Grok 的文档写了会读 Claude Code 的技能，
  没写是不是也这样（2026-09-30 查过）。
- 仓库 PR 权限是「有写权限的人才能提」。开 PR 报错先看是不是 PR 功能被整个关了。
