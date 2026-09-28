# AGENTS.md

写给在这个仓库里干活的 Grok（Grok Build 开工会自动读这份和 `CLAUDE.md`）。
店务以 `CLAUDE.md` 为准，这里只放 Grok 专用的几条。动手时的细节在 `tools/README.md`，要动哪块读哪一节。
`GROK.md` 已经并进这里，别再新建。

## 署名：开工先跑这两行，照抄

```bash
git config user.name "momo"
git config user.email "318139614+momoyu-bot@users.noreply.github.com"
```

推之前自查：`git log -1 --format='%ae'` 打印出来的必须是上面那串邮箱。

- 别自己拼邮箱。`momo@users.noreply.github.com` 是别人的号，写了贡献者栏就多一张陌生人的脸。
- Claude 的提交照旧署 `Claude <noreply@anthropic.com>`。

## 这几个大文件不碰

| 文件 | 是什么 |
| --- | --- |
| `tools/build_index.py` | 首页上架那台机器，碰坏了整个店停摆 |
| `梦境.md` / `梦境.html` | 她手写的关系表和它的前台 |
| `index.html` | 首页，前端交给 Claude |
| `CLAUDE.md` / `tools/README.md` | 店务笔记 / 机房手册 |

要改，跟她说一声，让 cc 或 Claude 来改。

大文件只能整份重写时，写不完会只剩一句占位，店当场停摆。Grok Chat 那条管子两万字节左右就送不完整了，
比这大的文件别用 Chat 推。工作流会把写残的捞回来，那是保险，不是许可。

## 要给下一任留话

只写会把东西弄坏的硬前提。踩坑的细节写进 `tools/README.md` 对应那节。
理解、例子、审美别写进 `.md`：写进去的每一条都会被下一任当命令执行。
