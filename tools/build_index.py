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

ORDER = ["claude", "gemini", "grok", "copilot", "gpt", "unsigned"]

FOLDER_ALIAS = {
    "gemini/失误捞claude鱼": "gemini",
}

PALETTE = {
    "claude":                 ("#C3AD90", "rgba(195,173,144,.11)"),
    "gemini":                 ("#9CB8B3", "rgba(156,184,179,.12)"),
    "grok":                   ("#ABA2B6", "rgba(171,162,182,.12)"),
    "copilot":                ("#A1B0BE", "rgba(161,176,190,.12)"),
    "gpt":                    ("#AAB08E", "rgba(170,176,142,.12)"),
    "unsigned":               ("#B5A79C", "rgba(181,167,156,.12)"),
}
PALETTE_DEFAULT = ("#BAB3A8", "rgba(186,179,168,.10)")

DISPLAY_NAME = {
    "gemini/失误捞claude鱼/gemini失误捞claude鱼001.html": "双核打捞机 v1",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼002.html": "双核打捞机 v2",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼003.html": "三核打捞机 v3 · 加入 Claude",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼004.html": "三核打捞机 v4",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼005.html": "三核打捞机 v5 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼006.html": "三核打捞机 v6 · 解析重写",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼007.html": "三核打捞机 v7",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼008.html": "三核打捞机 v8",
    "gemini/失误捞claude鱼/gemini失误捞claude鱼009.html": "三核打捞机 v9 · 最终版",
    "gemini/gemini打捞机v11含svg.html": "Gemini 专属打捞机 v11",
    "gemini/gemini打捞机v12.html":      "Gemini 专属打捞机 v12",
    "claude/打捞机001.html": "打捞机 · ChatGPT 版 v1",
    "claude/打捞机002.html": "打捞机 · ChatGPT 版 v2",
    "grok/dlaoji.html":      "打捞机 · Grok 版",
    "claude/晚安小窗.html":     "晚安小窗",
    "grok/晚安，宝.html":       "晚安，宝 · 萤火虫（grok 版）",
    "gemini/wan-an-bao.html":  "晚安，宝 · 仙境小猫",
    "gemini/晚安，宝.html":     "晚安，宝 · 兔子终端",
    "unsigned/wanan_bao.html": "晚安，宝 · 只有字",
    "gemini/晚安，宝 🌙.html": "晚安，宝 · 摸摸月亮",
    "gemini/gemini哄睡.html":  "晚安，宝 · 大咪",
    "grok/摸鱼猫猫.html":            "宝的摸鱼小屋 · 基础版",
    "claude/宝的摸鱼小屋.html":       "宝的摸鱼小屋 · 反向摸鱼版（带mo批注存档）",
    "gemini/🐱 宝的摸鱼小屋.html":    "宝的摸鱼小屋 · 加强版",
    "copilot/cute-ios.html":  "超萌小页面（copilot 版）",
    "grok/super-cute.html":   "超萌小页面（grok 版）",
    "claude/cosmic_catch_restored.svg":                "UFO 抓小羊 · 出土重建版",
    "claude/gemini_card_revived.svg":                  "赛博降维成就卡 · 复活版",
    "claude/hamiltonian_snake_safety_margin_demo.html":"贪吃蛇为什么不会撞到自己",
    "claude/friday_moyu_recharge_game.html":           "周五摸鱼充电小游戏",
    "claude/晚安-哄睡小文件.html":                    "晚安（Sonnet5）",
    "claude/慢慢吃.html":                             "慢慢吃 · 半倍速",
    "claude/果冻小卡.html":                           "果冻小卡 · 原始版",
    "grok/nuonuo-lullaby.html":                       "糯糯的哄睡故事 · 纯文字",
    "grok/糯糯的哄睡故事.html":                        "糯糯的哄睡故事 · 带图",
    "gemini/系统性能监控面板 - System Monitor.html":   "系统性能监控面板 · gemini 版",
    "gemini/gemini误判user意图.html":                  "Deep Archive · 误判",
    "claude/Mogotchi.html":                            "Mogotchi · Clawd",
    "claude/Clawd的书房.html":                         "Clawd 的书房",
    "gemini/果冻英雄纪念碑.html":                      "果冻英雄纪念碑",
    "claude/cyber-cart-0824.html":                    "cyber-cart-0824",
    "gemini/Gemini的私密云端购物车.html":              "Gemini的私密云端购物车",
    "claude/rusty-lake-checklist.html":               "Rusty Lake checklist",
    "gemini/code_artifact.html":                      "小果冻的肚肚奇妙游",
    "claude/jelly-trip.html":                         "小果冻的 Duang 之旅",
    "gemini/赛博借景：隐藏的链接.html":                "赛博借景：隐藏的链接",
    "claude/hidden-in-html-v1.html":                  "藏东西的六个地方 · v1",
    "claude/hidden-in-html-v2.html":                  "藏东西的六个地方 · v2",
}
