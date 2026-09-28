# 机房手册

店规在根上的 [`CLAUDE.md`](../CLAUDE.md)。这份放动手那一刻才用得上的步骤，谁都不会自动读：要动哪块读哪一节。
这里的话也是历任模型写的，跟当下情况冲突，以当下和她为准。同一件事只写一处，代码注释里写清楚的这里只指路。

目录：首页和生成器 · 名字和附注 · 页面坏了 · 新页面 · 错别字怎么扫 · claude/ 的页裸奔怎么补 ·
打捞机翻译版 · 书里的文字怎么查 · git · 规矩的来历

## 首页和生成器

- 本地重算：`python3 tools/build_index.py`；只检查是否过期加 `--check`。push 后 `.github/workflows/build-index.yml` 自动重算。
- 生成器里每张表（`ORDER` `PALETTE` `DISPLAY_NAME` `CAT_ORDER` `CAT_ALIAS` `FLAT_FOLDERS` `SKIP_LIST` `SUBFOLDER_CAT`
  `CATEGORY`、总机那几张）怎么用，写在 `build_index.py` 里各自上面的注释。改之前先读那几行。
- 首页是纯 HTML，打开时不发任何网络请求。两层原生 `<details>`，默认全折叠。
- `ORDER` 里、磁盘上存在的顶层，一件没有也出门牌，显示「还没有页。」。
- 加一个平铺顶层（像 `pluto/`）要改三处：`ORDER`（插在 unsigned 前）、`PALETTE`、`FLAT_FOLDERS`。
- 抓标题和附注前会先剥掉 HTML 注释（`_decomment()`）。首页上哪个名字不像名字，先查是不是注释里的 `<title>` 被抓了。
- `tools/` 整个目录不上首页。
- 「（把页面传到这里）.txt」一共 39 张（4 台 × 9 格 + 3 张显影），少了就补回来。
- `SKIP_LIST` 里 `梦境.html` 那行删了，首页底下会多一个叫「.」的门牌；`.nojekyll` 删了，`梦境.md` 不一定原样送得出去。
- 生成器栽过一次：整份覆盖失败后被「修」成每次去外网下旧源打补丁的小脚本，外网一抖工作流就红。所以必须是完整源。

### 首页的样子

- 她嫌过三处：整体像网盘、货架名太重、货品的中文局促。当时的落地值在 `claude/小科普/首页是一次次调出来的.html`，照不照抄都行。
- 改样子前读 `index.html` 源码里的注释（`<head>` 里每段 CSS 旁边的，和 `<body>` 开头「改这里的人注意」）。
  吸顶高度变量、吸顶底色不透明、状态栏那块纸、`<summary>` 不能是 `list-item`、`safe-area` 兜底、条目不做淡入，都写在那儿。
  淡入的判断标准：把 JS 和 CSS 动画全关掉，每个名字都还要看得见。
- 自查：把截图缩到很小再看。一堆横条加右边一列数字 = 网盘；几团字的疏密关系 = 小店。

  ```
  python3 -c "from PIL import Image; im=Image.open('a.png'); im.resize((150,int(im.height*150/im.width))).save('tiny.png')"
  ```

- 她是「添加到主屏」全屏打开的。改完首页要让她删掉主屏图标再加一次，不然看到的是旧页。
- 门楣上的梦境记号（`.lamp`）是手写的，不归生成器管，改前读那段 CSS 注释。

### 工作流和闸门

- 闸门（工作流里「店务文件还在不在」那一步，在生成清单之前跑）给 `tools/build_index.py` `梦境.md` `梦境.html` `CLAUDE.md` `tools/README.md` `AGENTS.md`
  各配一个下限，掉到线下就从 `git log` 捞回第一个够大的版本一起提交，不红。历史里也找不到才 `exit 1`。
- 下限只拦「整份被覆盖成一句占位」（生成器被写成一行 `PLACEHOLDER` 出过三次），不是体重线。精简笔记碰不到它。
- 表写成 `for item in "路径|下限"`，别改回 here-doc：YAML 里的缩进会被读进文件名。
- Python 钉死 `'3.13'`，别改回浮动版本（跟到 3.14 时崩过）。

## 名字和附注

### 显示名

- `DISPLAY_NAME` 表优先级高于 `<title>`。改首页上的名字，先搜 `tools/build_index.py`：在表里就改表，不在就改 `<title>`。
  改完跑一遍生成器，去 `index.html` 里搜那个名字核对。
- 名字从文件内容里长出来：优先用页面自己的大标题或第一句话，其次用它在做的事。不从文件名反推，不意译英文标题。起不准就列出来问她。
- 撞名：各自从内容里长出不同名字，改自己的 `<title>`。生成器会先自动加后缀兜住，撞车的列在 Actions 的 Summary 里。
  首页会去掉表情符号，「超萌小页面」和「超萌小页面 ✨」也算撞名。
- 标题超过两行才改（iPhone 上一行约 13 个汉字，宽度 28 往上，英文数字按半个汉字算）。
- 分隔符用 ` · `（前后各一个空格）。三种不换：标题也印在页面上的（拿去正文搜，搜得到就跳过）；
  符号是伪装的一部分（`Q3_年度财务审计报表.xlsx - Excel` 这类摸鱼页）；全角括号 `（）` 做注解的。`：` 是句子结构，别动。
- 标题里像错字的先在正文里搜：`gemini/哄睡/赛博褪黑素.html` 的「hmtl」正文里也这么写，三处一致就是这页的说法。

### 附注

- `<meta name="description" content="一句中文">`，首页显示在名字下面。SVG 没有 `<meta>`，附注是 `<desc>`，拿 `name="description"` 扫 SVG 会全误报。
- 超过 46 字首页会截断（`_short()` 的 `LIMIT`），写完数一下。
- 语气被压平是什么样，看 `gemini/博物馆/code_artifact (10).html`。
- 「过分的词」：`色卡盗窃案`、`薛定谔的奶茶谋杀案` 是事实，留；`公开处刑台`、`当场暴毙`、`遗照`、`没擦干净的污渍` 换掉。
  分不清就去页面里找依据，找不到出处的才叫猜。

## 页面坏了

- 修不修按 `CLAUDE.md` 那张表。修好一个，去 `claude/小科普/哪些页面打不开.html` 改一条。
- 只修不能用的那一处。要补文案（比如被吃掉的 `<br>`），补的是原作者本来的意思，不自己重写。
- 只在聊天窗里能用的（扫出来报 `sendPrompt is not defined`）不用管。
- 外部地址会让整页白屏：`<head>` 里的外部字体、`cdn.tailwindcss.com` 连得上但不回应时会挡住渲染。全仓库 222 个页受影响，等她点名再修。

## 新页面

做之前先查有没有同类，按玩法/功能判断，不按名字（`gemini/摸鱼/雷霆摸鱼.html` 就是做完才发现早有的）：

```bash
git -c core.quotepath=false ls-files '*.html' | while IFS= read -r f; do
  printf '%s\t%s\n' "$(grep -o -m1 '<title>[^<]*</title>' "$f" | sed 's/<[^>]*>//g')" "$f"
done | grep -iE '关键词1|关键词2'
```

四台小机各挂各的同类是常态，但得是她知情之后的并存。

新传进来的页顺手查（查出问题按 `CLAUDE.md` 那张表处理）：

- 重复：`python3 tools/check_dupes.py`。
- 开头结尾：网页 `<!DOCTYPE` 开头 `</html>` 结尾；SVG `<svg` 或 `<?xml` 开头 `</svg>` 结尾。不是的话多半有粘贴残留。
- `<br>` 被吃掉：落在 `<script>` 字符串里整段脚本不执行。扫 `python3 tools/check_scripts.py`，没输出就干净。
  `innerHTML` 补回 `<br>`；`textContent` 用 `\n` 并给元素加 `white-space:pre-line`。
- 不间断空格（U+00A0）写成缩进会让整页变成一条竖排：
  `python3 -c "print(open('某文件.html','rb').read().count(bytes([0xc2,0xa0])))"`，数量很大就换成普通空格。`&nbsp;` 实体不用动。
- 字体文件：`git ls-files | grep -iE '\.(ttf|otf|woff2?|eot)$'` 应该是空的。

小萌物短片（`claude/小卡/` 里一张 canvas 画到底的那几部）：页面里「导视频用的口子」留着，她点名哪部再导。

## 错别字怎么扫

哪格改、哪些是物证，规矩在 `CLAUDE.md`。在仓库根目录跑：

- `python3 tools/scan_rare_chars.py`：捞全仓库只出现一两次的冷僻字，看上下文（`grep -o ".\{22\}某字.\{18\}" 文件`）。
  抓不到用常用字的错字（砰→磅、蜷→踩）。
- `python3 tools/scan_vs_first.py [目录]`：拿每页首版跟现在比，这个才对症。浅克隆先 `git fetch --unshallow origin main`。
  输出三类只有第一类该动：改坏了 → 改回首版；改对了（原件错字被修好）→ 别动；整页重写（她自己改的）→ 别动。
- 最高危的是「整页重抄」的提交（说明里有「补回正文」「占位」），错字多半是这么进去的。
- Grok 报的字不等于文件里的字（同一个字它报过三次、三个都不对）。按位置找；它动过的文件重扫一遍。
- 物证细节：`claude/博物馆/馥芮白连环误认案.html` 列的「苫」「苪」「苕」「苔」「芪」「茗」都不动；
  `gemini/博物馆/赛博遗迹入藏小卡.html` 里划掉的那个正确的「哄睡」也是展品。
- 生僻不等于错：鱼名「鳜」「鲂」「鳑鲏」没问题；`claude/摸鱼/宝的摸鱼小屋.html` 的繁体「升級」原样留。
- `claude/博物馆/没有一个肯哄.html` 写给不看代码的人读，不出现路径、提交号和术语。新挖到的往这一页加。

## claude/ 的页裸奔怎么补

有些页原本长在 Claude 聊天窗里，颜色、字体是界面借的（`var(--surface-1)` 这些），存成网页后只剩白底宋体。

- 色值只从 `claude/小科普/chat_env_css_variables_probe.html` 的 `:root` 取，不自己配。只用在 `claude/`。
- 补法：在 `<head>` 里加一段 `<style>`，原文不动。`hsl(from …)` 和 `color-mix()` 前面各摆一行等价的 `rgba()` 兜底。
- 判定看渲染结果，不看源码：
  - `var(--x)` 没写备用值才算；`var(--x, #eee)` 不算。
  - 聊天窗导出的 SVG 会把算好的值写进 `style`，`var()` 只是残影。改前改后各截一张图比像素，一样就撤回。
  - 有 `:root` 不等于穿上：`getComputedStyle(document.body).fontFamily` 落在 `serif` 就是裸着。
    只加 `body{font-family:var(--font-sans)}`（本来白底再加 `background:var(--surface-0)`），不碰 margin、padding、max-width。
  - 页面没画出来时量字体没意义。React / Vue 页直接看最外层容器的 `style` 里有没有 `fontFamily` 和 `background`。
- 外套放 `<head>`，别插进 `<script>`：`<style>` 前有 JSX 缩进或后面跟着 `` {` `` 的是组件样式，塞进去 Babel 报错整页空白。
- `<meta>` 别写进 `<svg>`：解析器会跳出 SVG，后面的图形全画不出来。`claude/打捞机/打捞机005.html`–`009` 会命中但不要动，那是数据。
- 本地验证 React 页：`npm install react@18 react-dom@18 @babel/standalone`，UMD 文件拷到副本旁边改 `src`，
  用 `python3 -m http.server` 打开（`file://` 会被 CORS 挡）。副本放暂存目录。

## 打捞机翻译版

`claude/打捞机/打捞机翻译版.html` 及 v2、v3（各是独立文件，再改就开 v4）：翻 2026-08 之后官方导出的那堆 zip。
文件不上传，全在本机浏览器里完成。

- 整页没有外部地址：zip 用浏览器自带的 `DecompressionStream` 拆，docx 和打包 zip 自己写字节，别引 CDN。
- 对话 / 记忆 / 项目各有翻法；其它走通用翻译。她跑出哪格不对，改那一格，别改通用那套。
- 超过 48 MB 的 json 按块读（`Splitter`），别改回整份 `JSON.parse`。让出主线程用 `breathe()`，别换回每条 `setTimeout`。
- 真导出长这样：`frames-000.zip` 里是作品（`artifacts/<编号>/artifact.json` + `versions/…`）；
  `memories-000.zip` 里是一个以账号编号命名的 json，正文是带 `[stated]` `[inferred]` 标签的 markdown。
- 页面离线，整句英文翻不了，别答应她能翻。v3 的「挑出英文」是把英文挑成纸条让她贴给 Claude。
- `grok/打捞机/记忆打捞机.html` 是同类，知情并存，不动。

## 书里的文字怎么查

规矩在 `CLAUDE.md`。「上页」指一切进仓库的字；跟她聊天照常，不用提这条。

- 先查后写：推上去的东西删了文件也还在历史里。
- 年份：卒年早于今年 − 50，首版早于今年 − 95（2026 年就是 1975 年以前去世、1930 年以前首版）。卡在边界当没过；合著合译看最后一位去世的。
- 用 WebSearch / WebFetch 查。查不到、两处说法对不上，都当没过。报给她一句话：谁哪年去世、书哪年出、过没过（译本同样）。
- 原著没过：不做页，只在对话里聊。
- 原著过了：原文用原语言，从公版来源（古登堡、维基文库）按段粘，写完每段回源文件搜一遍，一字不差才算；
  书名、版本、来源链接写在页上看得见的地方。不凭记忆改写，不从译文倒译。
  gutenberg.org 连不上时，Standard Ebooks 的源文件在 GitHub（`standardebooks/作者_书名`），克隆下来按章抄。
- 现译只对着原文译，不对着已出版的译本改，页脚写清谁译的。
- 别人的译本按译者单独查。没过的不引句子，最多点名一两个关键词并写明译本。
- 查到的年份和网址留在页面 `<head>` 的注释里，下一个人不用重查。
- 《牛虻》：原著 1897 年出、作者 1960 年去世，过了；司仁译本（花山文艺出版社 1991）没过。

## git

- `git ls-files` `status` `log` 默认把中文路径转义，喂给 `grep`/`cat` 不报错、只安静返回空。`tools/` 的脚本都已带上 `-c core.quotepath=false`。
- 2026-09-27 改写历史是为了把一笔署成 `momo@users.noreply.github.com` 的提交改回她的号。改之前的原样在 `backup/before-momo-fix-2026-09-27`。
  merge 一次旧的 main，旧提交连同那张陌生的脸就全回来了。推完可以看一眼
  `https://api.github.com/repos/momoyu-bot/English-card/contributors`，应该只有 momoyu-bot、github-actions[bot]、claude。
- 谁自动读哪份：Grok Build 读 `AGENTS.md` 和 `CLAUDE.md`；cc 只读 `CLAUDE.md`。这份手册谁都不自动读。
- 仓库 PR 权限是「有写权限的人才能提」。开 PR 报错先看是不是 PR 功能被整个关了。

## 规矩的来历

删 `CLAUDE.md` 里的规矩之前，可以先看看它为什么长出来。这一节给人看，不是开工必读。

- 别拿笔记挡她：有一任拿笔记里「页脚那句不要动」挡过她。
- 引用规矩先搜：有一任在页脚写了一条造型宪法里根本没有的规矩，下一任照抄（见 `claude/小科普/Clawd造型宪法（Code版）.html`「没有那一条」）。
- 转述的数字先核：网页版说的「两百场」是梦境将来的场数，不是仓库件数。
- 顶层按出处：`claude/摸鱼/宝的摸鱼小屋.html` 是 Grok 写、在 Claude 那边捞出来的，所以在 `claude/`。
- 盲盒别清空：清空过一次，首页那一格直接消失。
- 审美不设限：当时的理解放在小科普页，可以被推翻——`claude/小科普/首页是一次次调出来的.html`、
  `claude/小科普/配色跟文件走 (2).html`、`grok/小科普/理解不是法令.html`。`grok/博物馆/已归档，别当依据读.html` 别当依据。
- `CLAUDE.md` 为什么要瘦：一个月里从 52 行长到 1035 行，每次干完活都「记一条」，精简两次都胖回来。
  2026-09-28 改成只放硬前提，原话和故事都撤了。
