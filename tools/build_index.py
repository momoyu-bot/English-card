#!/usr/bin/env python3
"""
重新生成 index.html 里的页面清单。

首页不再在打开时去问 GitHub 有哪些网页——清单在这里生成好，
直接写进 index.html。所以断网能看、GitHub 挂了能看、也不受
匿名接口每小时 60 次的限制。

用法：  python3 tools/build_index.py          # 写入 index.html
        python3 tools/build_index.py --check  # 只检查是否需要重新生成

这个脚本由 .github/workflows/build-index.yml 在每次 push 后自动跑，
不需要任何人记得手动执行。
"""

import os, re, sys, html, subprocess, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
BEGIN = "<!-- LIST:BEGIN 由 tools/build_index.py 自动生成，不要手改 -->"
END = "<!-- LIST:END -->"

# 分组顺序。没列到的目录排在后面，按名字排。
ORDER = ["claude", "gemini", "gemini/失误捞claude鱼", "grok", "copilot", "gpt", "unsigned"]

# 每个目录一种低饱和度的色，只用在悬停背景和小圆点上。
PALETTE = {
    "claude":                 ("#C3AD90", "rgba(195,173,144,.11)"),
    "gemini":                 ("#9CB8B3", "rgba(156,184,179,.12)"),
    "gemini/失误捞claude鱼":   ("#8FA9A4", "rgba(143,169,164,.12)"),
    "grok":                   ("#ABA2B6", "rgba(171,162,182,.12)"),
    "copilot":                ("#A1B0BE", "rgba(161,176,190,.12)"),
    "gpt":                    ("#AAB08E", "rgba(170,176,142,.12)"),
    "unsigned":               ("#B5A79C", "rgba(181,167,156,.12)"),
}
PALETTE_DEFAULT = ("#BAB3A8", "rgba(186,179,168,.10)")

# ---------------------------------------------------------------------------
# 显示名覆盖表
#
# 只写在这里一份。生成器直接把最终显示名写进 index.html，
# 首页里没有第二层查表。
#
# 出现在这张表里的，都是「多个页面 <title> 撞车、光看标题分不出谁是谁」的情况。
# 原文件的 <title> 一律不动——那是页面自己的标题，这里只管首页上显示成什么。
# ---------------------------------------------------------------------------
DISPLAY_NAME = {
    # 打捞机 · 九次迭代（gemini/失误捞claude鱼/）——原标题只有三种，分不出先后
    "gemini/失误捞claude鱼/gemini失误捞claude鱼001.html": "双核打捞机 v1",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼002.html": "双核打捞机 v2",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼003.html": "三核打捞机 v3 · 加入 Claude",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼004.html": "三核打捞机 v4",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼005.html": "三核打捞机 v5 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼006.html": "三核打捞机 v6 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼007.html": "三核打捞机 v7",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼008.html": "三核打捞机 v8",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼009.html": "三核打捞机 v9 · 最终版",

    # 打捞机 · 另外三个分支
    "claude/打捞机001.html": "打捞机 · ChatGPT 版 v1",
    "claude/打捞机002.html": "打捞机 · ChatGPT 版 v2",
    "grok/dlaoji.html":      "打捞机 · Grok 版",

    # 晚安，宝 —— 五个完全不同的页面，标题全一样
    "claude/晚安小窗.html":     "晚安，宝 · 萤火虫（claude 版）",
    "grok/晚安，宝.html":       "晚安，宝 · 萤火虫（grok 版）",
    "gemini/wan-an-bao.html":  "晚安，宝 · 仙境小猫",
    "gemini/晚安，宝.html":     "晚安，宝 · 兔子终端",
    "unsigned/wanan_bao.html": "晚安，宝 · 只有字",

    # 晚安，宝 🌙 —— 一个月亮一只猫
    "gemini/晚安，宝 🌙.html": "晚安，宝 · 摸摸月亮",
    "gemini/gemini哄睡.html":  "晚安，宝 · 大咪",

    # 摸鱼小屋 —— 基础版两份 + 加强版一份
    "grok/摸鱼猫猫.html":            "宝的摸鱼小屋 · 基础版",
    "claude/宝的摸鱼小屋.html":       "宝的摸鱼小屋 · 基础版（带批注存档）",
    "gemini/🐱 宝的摸鱼小屋.html":    "宝的摸鱼小屋 · 加强版",

    # 其余撞名
    # （下面两个原标题是「超萌小页面」和「超萌小页面 ✨」，
    #   首页会去掉表情符号，去掉之后就一模一样了）
    "copilot/cute-ios.html":  "超萌小页面（copilot 版）",
    "grok/super-cute.html":   "超萌小页面（grok 版）",

    "claude/慢慢吃.html":                             "慢慢吃 · 无倍速",
    "claude/果冻小卡.html":                           "果冻小卡 · 原始版",
    "grok/nuonuo-lullaby.html":                       "糯糯的哄睡故事 · 纯文字",
    "grok/糯糯的哄睡故事.html":                        "糯糯的哄睡故事 · 带图",
    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板 · gemini 版",
}

EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿︀-️"
    "\U0001F1E6-\U0001F1FF←-⇿⤀-⥿]"
)


def clean(text):
    text = EMOJI.sub("", str(text))
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ·、|-–—\t")


def prettify(filename):
    return clean(re.sub(r"\.html?$", "", filename, flags=re.I).replace("-", " ").replace("_", " "))


def page_title(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        head = fh.read(12000)
    m = re.search(r"<title[^>]*>([\s\S]*?)</title>", head, re.I)
    if not m:
        return ""
    return clean(html.unescape(m.group(1)))


def list_pages():
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "*.html"],
        cwd=ROOT, capture_output=True, text=True, check=True).stdout
    pages = []
    for rel in out.split("\n"):
        if not rel or rel == "index.html":
            continue
        if rel.split("/")[0].startswith(".") or rel.startswith("tools/"):
            continue
        pages.append(rel)
    return pages


def sort_key(name):
    # 中文按拼音排不了（标准库没有），退而求其次：按 Unicode 码位，
    # 但让纯 ASCII 开头的排在前面，跟原来的观感一致。
    return (0 if name[:1].isascii() else 1, name)


def build_entries():
    entries = []
    for rel in list_pages():
        folder = os.path.dirname(rel) or "."
        name = DISPLAY_NAME.get(rel) or page_title(os.path.join(ROOT, rel)) or prettify(os.path.basename(rel))
        entries.append({"path": rel, "folder": folder, "name": name})
    return entries


def group(entries):
    buckets = {}
    for e in entries:
        buckets.setdefault(e["folder"], []).append(e)

    def gkey(folder):
        return (ORDER.index(folder), "") if folder in ORDER else (len(ORDER), folder)

    blocks = []
    for folder in sorted(buckets, key=gkey):
        items = sorted(buckets[folder], key=lambda e: sort_key(e["name"]))
        blocks.append((folder, items))
    return blocks


def encode_path(rel):
    from urllib.parse import quote
    return "/".join(quote(part) for part in rel.split("/"))


def render(blocks):
    esc = lambda s: html.escape(s, quote=True)
    lines = [BEGIN]
    step = 0
    for folder, items in blocks:
        dot, tint = PALETTE.get(folder, PALETTE_DEFAULT)
        lines.append(f'  <section class="group" style="--dot:{dot};--tint:{tint}">')
        lines.append(f'    <h2 class="tag">{esc(folder)}</h2>')
        lines.append('    <ul class="list">')
        for e in items:
            delay = min(step * 40, 560)
            step += 1
            lines.append(
                f'      <li class="item" style="--delay:{delay}ms">'
                f'<a href="{encode_path(e["path"])}">{esc(e["name"])}</a></li>')
        lines.append("    </ul>")
        lines.append("  </section>")
    lines.append(END)
    return "\n".join(lines)


def main():
    entries = build_entries()
    blocks = group(entries)

    # 撞名自查：生成出来的显示名必须两两不同，否则首页上还是分不清
    seen = {}
    dup = []
    for e in entries:
        if e["name"] in seen:
            dup.append((e["name"], seen[e["name"]], e["path"]))
        seen[e["name"]] = e["path"]
    if dup:
        print("显示名还有撞车，请在 DISPLAY_NAME 里补上：", file=sys.stderr)
        for name, a, b in dup:
            print(f"  「{name}」\n      {a}\n      {b}", file=sys.stderr)
        return 2

    src = open(INDEX, encoding="utf-8").read()
    if BEGIN not in src or END not in src:
        print("index.html 里找不到 LIST 标记，无法写入", file=sys.stderr)
        return 3
    new = re.sub(re.escape(BEGIN) + r"[\s\S]*?" + re.escape(END), lambda _: render(blocks), src)

    if "--check" in sys.argv:
        if new != src:
            print("index.html 需要重新生成（跑 python3 tools/build_index.py）", file=sys.stderr)
            return 1
        print(f"index.html 是最新的（{len(entries)} 个页面）")
        return 0

    if new == src:
        print(f"index.html 无需改动（{len(entries)} 个页面）")
        return 0

    open(INDEX, "w", encoding="utf-8").write(new)
    print(f"index.html 已更新：{len(entries)} 个页面，{len(blocks)} 个分组")
    for folder, items in blocks:
        print(f"  {folder}/  {len(items)} 个")
    return 0


if __name__ == "__main__":
    sys.exit(main())
