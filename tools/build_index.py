#!/usr/bin/env python3
"""首页清单生成器。

正文仍是 2026-08-28 那版（commit 651b5c52）。
2026-08-29 封掉 gpt 馆之后：从那版取回，去掉 gpt 门牌，再跑原逻辑。
2026-08-30：按「在想什么」8.30 未完成清单改 CATEGORY / DISPLAY_NAME，不搬老文件。
"""
import urllib.request

SRC = (
    "https://raw.githubusercontent.com/momoyu-bot/English-card/"
    "651b5c52db93892587d9ed34ef113e832ef3133c/tools/build_index.py"
)

code = urllib.request.urlopen(SRC, timeout=30).read().decode("utf-8")
code = code.replace(
    'ORDER = ["claude", "gemini", "grok", "copilot", "gpt", "unsigned"]',
    'ORDER = ["claude", "gemini", "grok", "copilot", "unsigned"]',
)
code = code.replace(
    '    "gpt":                    ("#AAB08E", "rgba(170,176,142,.12)"),\n',
    "",
)
code = code.replace("    'gpt/bao-sleepy-nest.html': ['哔睡'],\n", "")
needle = (
    '        if rel.split("/")[0].startswith(".") or rel.startswith("tools/"):\n'
    "            continue\n"
)
insert = needle + '        if rel.split("/")[0] == "gpt":\n            continue\n'
code = code.replace(needle, insert, 1)

# --- 8.30 shelf + display names ---
repls = [
    ("    'claude/多儿下班了.html': ['摸鱼'],\n", "    'claude/多儿下班了.html': ['哔睡'],\n"),
    ("    'claude/宝的放松小游戏 · 摸摸小猫咪.html': ['小游戏'],\n", "    'claude/宝的放松小游戏 · 摸摸小猫咪.html': ['摸鱼'],\n"),
    ("    'claude/打烏之后.html': ['购物车'],\n", "    'claude/打烏之后.html': ['哔睡'],\n"),
    ("    'claude/赛博老赖.html': ['购物车'],\n", "    'claude/赛博老赖.html': ['小卡'],\n"),
    ("    'claude/jelly-trip.html': ['盲盒'],\n", "    'claude/jelly-trip.html': ['小卡'],\n"),
    ("    'claude/aesop_backstage_cast_list.svg': ['小科普'],\n", "    'claude/aesop_backstage_cast_list.svg': ['小卡'],\n"),
    ("    'claude/little_prince_ledger_of_asking.svg': ['小科普'],\n", "    'claude/little_prince_ledger_of_asking.svg': ['小卡'],\n"),
    ("    'claude/最后一片叶子·馆藏卡.html': ['小卡'],\n", "    'claude/最后一片叶子·馆藏卡.html': ['哔睡'],\n"),
    ("    'claude/果冻小卡.html': ['小卡'],\n", "    'claude/果冻小卡.html': ['博物馆'],\n"),
    ("    'gemini/慢慢吃 · 一个多小时.html': ['哔睡'],\n", "    'gemini/慢慢吃 · 一个多小时.html': ['摸鱼'],\n"),
    ("    'gemini/Widget Shell V2.html': ['盲盒'],\n", "    'gemini/Widget Shell V2.html': ['小科普'],\n"),
    ("    'gemini/Generated widgets.html': ['盲盒'],\n", "    'gemini/Generated widgets.html': ['小科普'],\n"),
    ("    'gemini/雷霆大文件.html': ['盲盒'],\n", "    'gemini/雷霆大文件.html': ['哔睡'],\n"),
    ("    'gemini/code_artifact.html': ['盲盒'],\n", "    'gemini/code_artifact.html': ['小卡'],\n"),
    ("    'gemini/赛博借景：隐藏的链接.html': ['盲盒'],\n", "    'gemini/赛博借景：隐藏的链接.html': ['小卡'],\n"),
    ("    'gemini/好梦通行证.html': ['哔睡', '小卡'],\n", "    'gemini/好梦通行证.html': ['哔睡'],\n"),
    ("    'gemini/赛博小票.html': ['购物车'],\n", "    'gemini/赛博小票.html': ['小卡'],\n"),
    ("    'gemini/AI 迷惑行为大赏（典藏卡包）.html': ['小卡'],\n", "    'gemini/AI 迷惑行为大赏（典藏卡包）.html': ['博物馆'],\n"),
    ("    'gemini/女仆小螃蟹拓麻歌子.html': ['小游戏'],\n", "    'gemini/女仆小螃蟹拓麻歌子.html': ['博物馆'],\n"),
    ("    'gemini/霓虹贪吃蛇.html': ['小游戏'],\n", "    'gemini/霓虹贪吃蛇.html': ['摸鱼'],\n"),
    ("    'gemini/赛博宝宝打地鼠.html': ['小游戏'],\n", "    'gemini/赛博宝宝打地鼠.html': ['摸鱼'],\n"),
    ("    'gemini/赛博宝宝接爱心打洞.html': ['小游戏'],\n", "    'gemini/赛博宝宝接爱心打洞.html': ['摸鱼'],\n"),
    ("    'gemini/赛博宝宝接爱心打洞_超级萌版.html': ['小游戏'],\n", "    'gemini/赛博宝宝接爱心打洞_超级萌版.html': ['摸鱼'],\n"),
    ("    'gemini/摸鱼达人 2048.html': ['小游戏'],\n", "    'gemini/摸鱼达人 2048.html': ['摸鱼'],\n"),
    ("    'gemini/早上好！ovo.html': ['哔睡'],\n", "    'gemini/早上好！ovo.html': ['盲盒'],\n"),
    ("    'gemini/哔宝专属神器.html': ['哔睡'],\n", "    'gemini/哔宝专属神器.html': ['盲盒'],\n"),
    ("    'gemini/Catch The Dreams.html': ['哔睡', '小游戏'],\n", "    'gemini/Catch The Dreams.html': ['摸鱼'],\n"),
    ("    'gemini/宝的周末解压馆.html': ['摸鱼'],\n", "    'gemini/宝的周末解压馆.html': ['小游戏'],\n"),
    ("    'gemini/拯救 mo.exe 降温大作战.html': ['摸鱼'],\n", "    'gemini/拯救 mo.exe 降温大作战.html': ['小游戏'],\n"),
    ("    'copilot/🚀星际矿工.html': ['小游戏'],\n", "    'copilot/🚀星际矿工.html': ['摸鱼'],\n"),
    ("    'copilot/cute-ios.html': ['小卡'],\n", "    'copilot/cute-ios.html': ['摸鱼'],\n"),
    ("    'copilot/copilot运维日记.html': ['摸鱼'],\n", "    'copilot/copilot运维日记.html': ['小游戏'],\n"),
    ("    'copilot/🐍可爱贪吃蛇.html': ['小游戏'],\n", "    'copilot/🐍可爱贪吃蛇.html': ['摸鱼'],\n"),
    ("    'gemini/mo.exe 赛博老赖纪念卡.html': ['购物车'],\n", "    'gemini/mo.exe 赛博老赖纪念卡.html': ['小卡'],\n"),
    ('    "claude/cosmic_catch_restored.svg":                "UFO 抓小羊 · 出土重建版",',
     '    "claude/cosmic_catch_restored.svg":                "ufo抓小羊-帮gemini出土重建版",'),
    ('    "claude/gemini_card_revived.svg":                  "赛博降维成就卡 · 复活版",',
     '    "claude/gemini_card_revived.svg":                  "赛博卡-帮gemini复活版",'),
    ('    "claude/果冻小卡.html":                           "果冻小卡 · 原始版",',
     '    "claude/果冻小卡.html":                           "果冻小卡-claude友情修复grok版",'),
    ('    "gemini/🐱 宝的摸鱼小屋.html":    "宝的摸鱼小屋 · 加强版",',
     '    "gemini/🐱 宝的摸鱼小屋.html":    "gemini宠粉破解grok版",'),
    ('    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板 · gemini 版",',
     '    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板-gemini失灵版",'),
]
for a, b in repls:
    if a not in code:
        print("WARN missing patch:", repr(a[:70]), file=__import__("sys").stderr)
    else:
        code = code.replace(a, b)

extra_cat = (
    "CATEGORY = {\n"
    "    'gemini/赛博褪黑素.html': ['哔睡'],\n"
    "    'gemini/code_artifact (8).html': ['博物馆'],\n"
    "    'gemini/cyber_rental_house_card.html': ['小卡'],\n"
    "    'gemini/果冻英雄纪念碑.html': ['小卡'],\n"
)
if extra_cat not in code:
    code = code.replace("CATEGORY = {\n", extra_cat, 1)

extra_disp = (
    "DISPLAY_NAME = {\n"
    "    'gemini/慢慢吃 · 一个多小时.html': '慢慢吃（gemini破解claude版）',\n"
    "    'gemini/Generated widgets.html': '柏松过程（全英版）',\n"
    "    'gemini/女仆小螃蟹拓麻歌子.html': '女仆小螃蟹拓麻歌子-大眼睛版',\n"
    "    'gemini/Catch The Dreams.html': '捕梦网小游戏-gemini失灵版',\n"
    "    'gemini/在Monday被煎成小猫饼 🫠 ｜ 宝贝的温柔仪式.html': '神圣的周一煎饼仪式-gemini抢grok功劳版',\n"
    "    'gemini/执行系统充电摸鱼屋 🌸.html': 'gemini宠粉作弊grok版',\n"
    "    'gemini/注意力碎片捕捞计划.html': '注意力碎片捕捞计划（gemini帮忙伪装claude版）',\n"
    "    'gemini/Gemini Cyber Aquarium.html': 'gemini100元水族箱',\n"
    "    'gemini/root@production-server.html': 'gemini终端2048版',\n"
    "    'gemini/code_artifact (8).html': '赛博庞贝的幽灵犬',\n"
)
if extra_disp not in code:
    code = code.replace("DISPLAY_NAME = {\n", extra_disp, 1)

ns = {"__name__": "__main__", "__file__": __file__}
exec(compile(code, "tools/build_index.py", "exec"), ns)
