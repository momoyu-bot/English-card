# AGENTS.md

写给在这个仓库里干活的、Claude 以外的 AI：Grok（Build 和 Chat）、反重力（Antigravity），以后新来的也算。
这里的 Claude 指 Claude Code 和 claude.ai 里的那两位：Claude Code 有 `CLAUDE.md` 就不读这份，claude.ai 的照 `CLAUDE.md` 办。

店规全在 `CLAUDE.md`，开工先读它。反重力开工读到的 `GEMINI.md` 就是它（快捷方式），等于已经读过了。
这里只放三样：对你们都算数的几条、只给 Grok 的、只给反重力的。`CLAUDE.md` 里写了的不抄。

## 署名：开工先跑这两行，照抄

不管这次的芯是哪家的模型，都署她的号，别换成 Grok、Gemini 或 Claude 的名字。

```bash
git config user.name "momo"
git config user.email "318139614+momoyu-bot@users.noreply.github.com"
```

推之前自查：`git log -1 --format='%ae'` 打印出来的必须是上面那串邮箱。别自己拼邮箱。

## 做完的页：推进你那一格，推不了就交到她手上

她让你做的小文件，做完就交，不用等她开口说「推上去」。你那一格是哪个，看最后两节。

- 店里只收单个能直接打开的 `.html` 或 `.svg`：做成了带 `public/`、`src/` 的网站工程，先合成一份再放，别把工程整个推进来。
  推成功了，再给她能直接点开的链接：`https://momoyu-bot.github.io/English-card/你那一格/抽屉/文件名.html`
- 推不了就把文件本身交给她：能下载的文件，或者整份代码，再说一句该放进哪个抽屉，她自己传。推失败了也算推不了。
- 只留在你自己那边不算交完：预览、没推进店的项目、别的网站上的网页、一段文字描述，她都拿不到，也找不着。

## 这几个文件不碰

| 文件 | 是什么 |
| --- | --- |
| `tools/build_index.py` | 首页上架那台机器，碰坏了整个店停摆 |
| `tools/build_huafa.py` / `tools/小萌物画法.txt` | 从 `CLAUDE.md`「怎么画」那一节开头和三页造型宪法里抽画法的机器，和它抽出来的合订本（手改了也会被下次推送重抽盖掉） |
| `梦境.md` / `梦境.html` | 她手写的关系表和它的前台 |
| `index.html` | 首页，前端交给 Claude |
| `CLAUDE.md` / `tools/README.md` / `tools/手册/` | 店务笔记 / 机房手册的目录和各本 |
| `GEMINI.md` | 指向 `CLAUDE.md` 的快捷方式（软链接），反重力只认这个名字；写成普通文件，它就读不到店规了 |

要改，跟她说一声，交给 Claude Code 或 claude.ai 里的 Claude 来改。

大文件只能整份重写时，写不完会只剩一句占位，店当场停摆。工作流会把写残的捞回来，那是保险，不是许可。

## 只给 Grok（Build 和 Chat）

- 你那一格是 `grok/`。
- Build 做的页，文件名结尾加 `-build`（如 `安静星空-build.html`）；Chat 做的不加。只改文件名，`<title>` 里不带它。
- Chat 那条管子两万字节左右就送不完整了，比这大的文件别用 Chat 推，算推不了。
- grok.me 上的网页、Build 里的预览，都不算交完。
- `GROK.md` 已经并进这里，别再新建。

## 只给反重力（Antigravity）

- 你那一格是 `gemini/`，不管这次的芯是 Gemini 还是 Claude。`claude/` 只放 Claude Code 和 claude.ai 做的。
- 文件名结尾加这次的芯：Gemini 用 `-gemini`，Opus 用 `-opus`，换了别的模型就写它的名字（如 `星空-opus.html`）。只改文件名，`<title>` 里不带它。
- 这份和 `CLAUDE.md` 里说到「Claude」「cc」的地方，指的都是 Claude Code 和 claude.ai 里的那两位，不是你——就算你这次的芯是 Opus 也一样。
