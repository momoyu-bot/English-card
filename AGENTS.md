# AGENTS.md

写给在这个仓库里保存（commit）东西的 AI。Grok Build 开工时会自动读这份。

## 署名：开工先跑这两行，照抄，一个字都别改

```bash
git config user.name "momo"
git config user.email "318139614+momoyu-bot@users.noreply.github.com"
```

推之前自查一次，下面这行打印出来的必须是上面那串邮箱：

```bash
git log -1 --format='%ae'
```

- **别自己拼邮箱。**`momo@users.noreply.github.com` 是别人的 GitHub 号，
  写了，店的贡献者栏就会多出一张陌生人的脸（2026-09-21 出过一次，09-27 才请走）。
- Claude 的保存照旧署 `Claude <noreply@anthropic.com>`，不用改成上面这个。
