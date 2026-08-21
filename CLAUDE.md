# English-card 工作笔记

宝的英语打卡 / 哄睡 / 摸鱼小页面收藏。每个子文件夹记的是**页面从哪个对话里捞出来的**，
不是"谁写的"——所以 `claude/` 里出现 Grok 写的东西是正常的，不算放错。

**实例：** `claude/宝的摸鱼小屋.html` 是 Grok 写的，却在 `claude/` 目录里，
因为当时是拿这份代码去问 Claude 为什么报错。文件末尾用 HTML 注释保留了
当时那句原话。判断归属时不要按"内容像谁写的"去挪文件。

**例外：** `grok/女仆小螃蟹 Tamagotchi 小机.html` 是 Grok 看了 Claude 的 Mogotchi
之后做的山寨（和 `grok/空心树值班.html` 同一类）。原从 Claude 对话捞出，
曾在 `claude/`；2026-08-21 按她本人的判断挪到 `grok/`，文件里有注释。

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

导入时还要顺手检查三件事：

1. **`<br>` 有没有被吃掉。**有几份副本里 `<br>` 被替换成了普通换行，
   而 HTML 里普通换行等于空格——换行效果直接消失。
2. **粘贴残留。**导入后确认文件以 `<!DOCTYPE` 开头、以 `</html>` 结尾。
3. **不间断空格（U+00A0）。**`claude/宝的摸鱼小屋.html` 曾经把缩进全写成
   U+00A0。CSS 不认它当空白，整页变成一条竖排。比对：
   `python3 -c "print(open('某文件.html','rb').read().count(bytes([0xc2,0xa0])))"`
   若数量很大，把 `\u00a0` 换成普通空格。内容里的 `&nbsp;` 实体不用动。

## 首页 index.html —— 不要手改清单

首页里那份清单由 `tools/build_index.py` 生成，写在 `<!-- LIST:BEGIN -->`
和 `<!-- LIST:END -->` 之间。**手改会在下次 push 时被覆盖。**

- 加了/删了/改名了页面，push 上去就行，
  `.github/workflows/build-index.yml` 会自动重算清单并提交回来。
- 本地想立刻更新：`python3 tools/build_index.py`；
  只想检查是否过期：`python3 tools/build_index.py --check`。
- 首页现在是纯 HTML，打开时**不发任何网络请求**——断网能看，
  GitHub 挂了也能看。二级分类用原生 `<details>`/`<summary>`，不写 JS。
- 目录层级不限，`目录/子目录/文件.html` 也会被列出来。

### 两个页面标题撞车了怎么办

**不要改页面自己的 `<title>`。**在 `tools/build_index.py` 的
`DISPLAY_NAME` 表里加一行，写清首页上要显示成什么。生成器带自查：
只要有两个页面的最终显示名相同，就会报错退出、拒绝生成，
把撞车的两个路径打印出来。

注意首页会去掉标题里的表情符号，所以「超萌小页面」和「超萌小页面 ✨」
去掉之后是同一个名字——这类撞车肉眼看不出来，靠那个自查兜住。

### 二级分类

按「什么时候会点开」切，写在 `tools/build_index.py` 的 `CATEGORY` 表里。
现用：哄睡 / 摸鱼 / 小游戏 / 赛博购物车 / 科普 / 凭证 / 障眼法 / 打捞机 / 盲盒。
（早安并入哄睡；不上班这一档。）
一个文件可以同时属于两档。`unsigned/` 只有一级，平铺。
`gemini/失误捞claude鱼/` 不单独成一级，归进 gemini 下面的「打捞机」。
改分类只改 `CATEGORY`，再跑生成器——不要手改 index.html 里的清单。

首页是两层原生 `<details>`，默认全折叠：先看到六个小机名字，点开才看到二级，再点开才看到条目。

标题（英语打卡小页面）和页脚（慢慢来，一天一张就够了）不要动。

## 公开仓库，注意别写真东西

这个仓库是公开的，`momoyu-bot.github.io/English-card/` 直接可访问。
里面有多个伪装成工作文件的摸鱼小游戏，写假数据时避开：
真实公司名、真实人名、真实商品搜索词、能反推业务的关键词。
