# English-card 工作笔记

宝的英语打卡 / 哄睡 / 摸鱼小页面收藏。每个子文件夹记的是**页面从哪个对话里捞出来的**，
不是"谁写的"——所以 `claude/` 里出现 Grok 写的东西是正常的，不算放错。

## ⚠️ 批量导入打捞回来的页面之前，必须先比对指纹

2026-08 的两次批量导入（`1e7536c` 把 Grok 对话里捞的放进 `grok/`、
`110ca66` 把 Claude 对话里捞的放进 `claude/`）没有先跟仓库里已有的文件比对，
一次性造成了 **8 组重复文件**。以后再导入，先跑这一步：

```bash
# 比对前必须先统一行尾，否则 CRLF/LF 差异会让同一份内容算出不同指纹
python3 - <<'PY'
import subprocess, hashlib, collections, pathlib
files = [f for f in subprocess.run(
    ['git','-c','core.quotepath=false','ls-files','*.html'],
    capture_output=True, text=True).stdout.split('\n') if f]
seen = collections.defaultdict(list)
for f in files:
    b = open(f,'rb').read().replace(b'\r\n', b'\n').replace(b'\r', b'\n').strip()
    seen[hashlib.md5(b).hexdigest()].append(f)
for k, v in seen.items():
    if len(v) > 1:
        print('重复:', *v, sep='\n  ')
PY
```

**为什么必须统一行尾再比：** 从聊天记录导出的文件常带 Windows 式行尾（CRLF），
手工添加的是 LF。同样的内容用两种行尾存出来，肉眼一模一样，`md5` 却不同——
直接按原始指纹去找重复，会漏掉绝大部分。上面那 8 组里有 6 组就是这么漏掉的。

导入时还要顺手检查两件事：

1. **`<br>` 有没有被吃掉。**有几份副本里 `<br>` 被替换成了普通换行，
   而 HTML 里普通换行等于空格——换行效果直接消失。
2. **粘贴残留。**`claude/宝的摸鱼小屋.html` 开头多了个 `<`、结尾多了个 `>`
   加一行对话原文。导入后确认文件以 `<!DOCTYPE` 开头、以 `</html>` 结尾。

## 首页 index.html

首页不是写死的清单：打开时去 GitHub 接口实时问仓库里有哪些网页，再逐个读标题当链接文字。

- 加载器只认 `目录/文件.html` 这一层，更深的路径会被跳过。
- GitHub 对不登录的接口调用限制是**每个网络地址每小时 60 次**，
  且额度按出口地址共享——公司/咖啡馆 Wi-Fi 下可能被别人用完。

## 公开仓库，注意别写真东西

这个仓库是公开的，`momoyu-bot.github.io/English-card/` 直接可访问。
里面有多个伪装成工作文件的摸鱼小游戏，写假数据时避开：
真实公司名、真实人名、真实商品搜索词、能反推业务的关键词。
