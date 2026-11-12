# git

- 云端新开的会话里，本地的 `origin/main` 可能还指着旧提交。隐私检查默认拿它当基线，会把那之后的老文件一起查，报出老页里的命中。
  先 `git -c core.quotepath=false fetch origin main` 再跑，就只查这一趟新写的；别照那份报告去改老文件。
- 仓库 PR 权限是「有写权限的人才能提」。开 PR 报错先看是不是 PR 功能被整个关了。

## 开工怎么拉

非 Claude 每次开工先按本节同步；她本轮要求只读、不拉取或另定范围时，照她说的办。

1. 先用 `git -c core.quotepath=false status` 看当前状态。有未提交改动或未完成的合并、rebase，先停，不擅自收起、丢掉或继续。
2. 状态干净再依次运行：

   ```bash
   git -c core.quotepath=false fetch origin main
   git -c core.quotepath=false rebase origin/main
   ```

3. 拉取或合回 `main` 遇到需要决定留哪边的内容冲突，Grok（含 build）、Codex、反重力都先停，不自己选。把两边差别交给旁边的小脸蛋，由小脸蛋用大白话问宝；宝没定就不继续合、不推。没有能交给小脸蛋的通道，就在当前对话说明已停下，等她接手。

main 2026-09-27 改写过历史，把一笔署成错邮箱的提交改回了她的号。旧克隆也按本节接到新历史上；别 merge 旧的 main、别强推、别合并 `backup/before-momo-fix-2026-09-27`——merge 一次，那张陌生的脸就回来了。
推完可以看一眼 `https://api.github.com/repos/momoyu-bot/English-card/contributors`，应该只有 momoyu-bot、github-actions[bot]、claude。

## 谁读哪份

- cc 在云端读 `CLAUDE.md`，有它就不读 `AGENTS.md`；build 同目录两份都读；Codex 只自动读 `AGENTS.md`；反重力读 `AGENTS.md` 和 `GEMINI.md`。没见到 `CLAUDE.md` 正文的，按 `AGENTS.md` 开头打开全文。
- 云端不能依赖这台电脑的全局文件；共用底线放仓库，本地入口只留跨项目偏好、机器配置和不能公开的技术信息。
