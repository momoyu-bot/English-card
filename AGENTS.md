# AGENTS.md

给 Claude 以外的 AI：Grok（Build 和 Chat）、反重力、Codex，以后新来的也算。Claude 指谁见 `CLAUDE.md`；cc 有它就不读本文件，claude.ai 也照它办。本文件只放非 Claude 的共同要求和各家差异。
开工必须确认已读到本轮仓库 `CLAUDE.md` 全文：没看到正文就不算读过，先打开从头读完再动手。已完整自动加载的（如 build）不用重复读；只有文件名、摘要或上次记忆都不算。
- 底线：严禁把任何隐私写进公开仓库或提交说明，完整清单见 CLAUDE.md。
- 提交前必跑 `tools/check_dupes.py`、`tools/check_scripts.py`、`tools/check_privacy.py`，三个都通过才提交；Windows 用 `py -3.13`，云端用 Python 3.13。
- 云端读不到本机全局文件也照样遵守这两条，不能拿本地副本代替仓库正文。

## 对非 Claude 都算数

- 开工先照抄 `CLAUDE.md`「git」里的两条署名命令；不管芯是谁都署她的号，推前照那一节自查邮箱，别自己拼。
- 开工先 `git -c core.quotepath=false pull` 同步 GitHub 最新版，这不算改旧文件；Grok、反重力拉取有冲突先停下，用中文大白话说明，再一起决定保留哪个版本。
- **只加不改**：已有文件（包括自己以前推的）不改、不删、不挪、不改名。想动先说动哪里、为什么，她点头再动；她这一轮亲口让改的已算授权。这条高于 CLAUDE.md 及手册里叫你挪、改、删、补的说法。
- 下列文件默认不碰；要改先跟她说，交给 Claude Code 或 claude.ai 的 Claude，除非她这一轮明确授权你改：
  `tools/build_index.py`（首页上架机器）；`tools/build_huafa.py` / `tools/小萌物画法.txt`（从店规和三页宪法抽画法的机器及合订本，手改合订本会被重抽覆盖）；
  `梦境.md` / `梦境.html`（她手写的关系表和前台）；`index.html`（首页前端交给 Claude）；`CLAUDE.md` / `tools/README.md` / `tools/手册/`（店务笔记和机房手册）；`GEMINI.md`（指向 CLAUDE.md 的软链接，不能写成普通文件）。
- 大文件只能整份重写而写不完，会剩一句占位让店停摆；工作流捞回写残文件是保险，不是许可。
- 她让做的小文件做完就交，不用等她说推；只收单个能直接打开的 `.html` 或 `.svg`。带 `public/`、`src/` 的工程先合成一份再放，别把工程整个推进来。
- 推成功给直达链接：`https://momoyu-bot.github.io/English-card/你那一格/抽屉/文件名.html`。推不了（含推失败）就交可下载的文件或整份代码，并说放哪个抽屉，她自己传。
- 只留预览、没进店的项目、别的网站上的网页或文字描述，都不算交完。反重力获准改完也直接提交、推送，推完用中文说改了什么；她本轮另定交付时机的照她说的办。

## 只给 Grok（Build 和 Chat）

- 进 `grok/`。Build 文件名结尾加 `-build`（如 `安静星空-build.html`），Chat 不加；只改文件名，`<title>` 不带后缀。
- Chat 那条管子约两万字节就送不全，比这大的别用 Chat 推，算推不了；grok.me 网页和 Build 预览都不算交完。`GROK.md` 已并进这里，别再新建。

## 只给反重力（Antigravity）

- 进 `gemini/`，按壳不按芯；`claude/` 只放 Claude Code 和 claude.ai 的。文件名结尾按芯加：Gemini 用 `-gemini`，Opus 用 `-opus`，别的写实际模型名（如 `星空-opus.html`），`<title>` 不带它。
- Windows 上若 `GEMINI.md` 只剩一行 `CLAUDE.md`，那是软链接落成了目标文件名，不是店规正文；按开头要求打开 CLAUDE.md，那一行字别改、别提交。

## 只给 Codex

- 进 `codex/`；文件名结尾加 `-codex`（如 `星空-codex.html`），`<title>` 不带它。仓库只自动读本入口，CLAUDE.md 不会自动展开，必须按开头要求读全文。
- 推到 `main` 才上架；在 worktree 或别的分支上做的，合回 `main` 再推，只推别的分支不算交完。
