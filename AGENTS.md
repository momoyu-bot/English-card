# AGENTS.md

给 Claude 以外的 AI：Grok（Build 和 Chat）、反重力、Codex，以后新来的也算。Claude 指谁见 `CLAUDE.md`；cc 有它就不读本文件，claude.ai 也照它办。本文件只放非 Claude 的共同要求和各家差异。
开工先确认上下文里有本轮仓库 `CLAUDE.md` 的全文，没有就打开从头读完再动手。完整自动加载、还没被压缩掉的算有（如 build）；只有文件名、摘要、上次的记忆，或压缩后只剩摘要，都不算。
- 底线：严禁把任何隐私写进公开仓库或提交说明，完整清单见 CLAUDE.md。
- 提交前必跑 `tools/check.py`，通过才提交；云端用 Python 3.13 的 `python3`，Windows 用 `py -3.13`。
- 云端读不到本机全局文件也照样遵守这两条，不能拿本地副本代替仓库正文。

## 对非 Claude 都算数

- 署名：不管芯是谁都署她的号。开工先照抄下面两行，别自己拼邮箱，别写 `momo@users.noreply.github.com`，那是别人的号。
  推之前用 `git -c core.quotepath=false log -1 --format='%ae'` 自查，必须跟这里配置的邮箱完全一致。

  ```bash
  git -c core.quotepath=false config user.name "momo"
  git -c core.quotepath=false config user.email "318139614+momoyu-bot@users.noreply.github.com"
  ```

- 开工先按 `tools/手册/git.md`「开工怎么拉」同步，这不算改旧文件的授权；拉取或合回 `main` 遇到内容冲突，先按该节交给小脸蛋问宝，不自己选。她本轮要求只读或不拉取的照她说的办。
- **只加不改**：已有文件（包括自己以前推的）不改、不删、不挪、不改名。想动先说动哪里、为什么，她点头再动；她这一轮亲口让改的已算授权。这条高于 CLAUDE.md 及手册里叫你挪、改、删、补的说法。
- 下列文件默认不碰；要改先跟她说，交给 Claude Code 或 claude.ai 的 Claude，除非她这一轮明确授权你改：
  `tools/build_index.py`（首页上架机器）；`tools/build_huafa.py` / `tools/小萌物画法.txt`（从店规和三页宪法抽画法的机器及合订本，手改合订本会被重抽覆盖）；
  `梦境.md` / `梦境.html`（她定的关系表和前台）；`index.html`（首页前端交给 Claude）；`CLAUDE.md` / `tools/README.md` / `tools/手册/`（店务笔记和机房手册）；`GEMINI.md`（指向 CLAUDE.md 的软链接，不能写成普通文件）。
- 大文件只能整份重写而写不完，会剩一句占位让店停摆；工作流捞回写残文件是保险，不是许可。
- 她让做的小文件做完就交，不用等她说推；只收单个能直接打开的 `.html` 或 `.svg`。带 `public/`、`src/` 的工程先合成一份再放，别把工程整个推进来。
  GIF 馆例外：馆页旁边带一个同名文件夹放 GIF，图片不许转成 Base64 写进网页，细则见 `tools/手册/GIF馆.md`。
- 推成功给直达链接就算交完，不用等首页更新，也不用打开线上页面再看：`https://momoyu-bot.github.io/English-card/你那一格/抽屉/文件名.html`。推不了（`git push` 失败一次就算，别再改走 GitHub 插件或别的接口重传）就交可下载的文件（给不了文件再贴整份代码），并说放哪个抽屉，她自己传。
- 只留预览、没进店的项目、别的网站上的网页或文字描述，都不算交完。反重力获准改完也直接提交、推送，推完用中文说改了什么；她本轮另定交付时机的照她说的办。

## 只给 Grok（Build 和 Chat）

- 进 `grok/`。Build 文件名加 `-build`（如 `安静星空-build.html`），Chat 不加；只改文件名，`<title>` 不带后缀。
- Chat 那条管子约两万字节就送不全，比这大的别用 Chat 推，算推不了；grok.me 网页和 Build 预览都不算交完。`GROK.md` 已并进这里，别再新建。

## 只给反重力（Antigravity）

- 进 `gemini/`，按壳不按芯；`claude/` 只放 Claude Code 和 claude.ai 的。文件名按芯加：Gemini 用 `-gemini`，Opus 用 `-opus`，别的写实际模型名（如 `星空-opus.html`），`<title>` 不带它。
- Windows 上若 `GEMINI.md` 只剩一行 `CLAUDE.md`，那是软链接落成了目标文件名，不是店规正文；按开头要求打开 CLAUDE.md，那一行字别改、别提交。

## 只给 Codex

- 进 `codex/`；文件名加 `-codex`（如 `星空-codex.html`），`<title>` 不带它。仓库只自动读本入口，CLAUDE.md 不会自动展开，必须按开头要求读全文。
- 推到 `main` 才上架；在 worktree 或别的分支上做的，合回 `main` 再推，只推别的分支不算交完。
- 只有在 ChatGPT Work 里做的不推，交文件就算交完：写出能播的第一版先交一份，查完改完、跑过开头那项检查再交终版，说放哪个抽屉，她自己传。终端和 Codex Cloud 都照上一条推；在云端跑不等于在 Work 里。
