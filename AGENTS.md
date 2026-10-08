# AGENTS.md

写给在这个仓库里干活的 Grok。Grok Build 开工会把这份和 `CLAUDE.md` 一起读进来：店务以 `CLAUDE.md` 为准，
这里只放 Grok 专用的几条，不抄那边已经写了的。`GROK.md` 已经并进这里，别再新建。

## 署名：开工先跑这两行，照抄

```bash
git config user.name "momo"
git config user.email "318139614+momoyu-bot@users.noreply.github.com"
```

推之前自查：`git log -1 --format='%ae'` 打印出来的必须是上面那串邮箱。别自己拼邮箱。

## 做完的页：推进店里，推不了就交到她手上

她让你做的小文件，做完就交，不用等她开口说「推上去」：

- 能推就推进 `grok/` 里它该在的抽屉。店里只收单个能直接打开的 `.html` 或 `.svg`：Build 做成了带 `public/`、`src/` 的网站工程，
  先合成一份再放，别把工程整个推进来。推成功了，再给她能直接点开的链接：
  `https://momoyu-bot.github.io/English-card/grok/抽屉/文件名.html`
- 推不了就把文件本身交给她：能下载的文件，或者整份代码，再说一句该放进哪个抽屉，她自己传。
  在 Chat 里、文件超过两万字节（见最后一段），或者推失败了，都算推不了。
- 只留在你自己那边不算交完：Build 里的预览、没推进店的项目、grok.me 上的网页、一段文字描述，她都拿不到，也找不着。

## 这几个文件不碰

| 文件 | 是什么 |
| --- | --- |
| `tools/build_index.py` | 首页上架那台机器，碰坏了整个店停摆 |
| `tools/build_huafa.py` / `tools/小萌物画法.txt` | 从 `CLAUDE.md`「怎么画」那一节开头和三页造型宪法里抽画法的机器，和它抽出来的合订本（手改了也会被下次推送重抽盖掉） |
| `梦境.md` / `梦境.html` | 她手写的关系表和它的前台 |
| `index.html` | 首页，前端交给 Claude |
| `CLAUDE.md` / `tools/README.md` / `tools/手册/` | 店务笔记 / 机房手册的目录和各本 |

要改，跟她说一声，让 cc 或 Claude 来改。

大文件只能整份重写时，写不完会只剩一句占位，店当场停摆。Grok Chat 那条管子两万字节左右就送不完整了，
比这大的文件别用 Chat 推。工作流会把写残的捞回来，那是保险，不是许可。
