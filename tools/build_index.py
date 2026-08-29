#!/usr/bin/env python3
"""首页清单生成器。

正文仍是 2026-08-28 那版（commit 651b5c52）。
2026-08-29 封掉 gpt 馆之后：从那版取回，去掉 gpt 门牌，再跑原逻辑。
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
code = code.replace("    'gpt/bao-sleepy-nest.html': ['哄睡'],\n", "")
needle = (
    '        if rel.split("/")[0].startswith(".") or rel.startswith("tools/"):\n'
    "            continue\n"
)
insert = needle + '        if rel.split("/")[0] == "gpt":\n            continue\n'
code = code.replace(needle, insert, 1)

ns = {"__name__": "__main__", "__file__": __file__}
exec(compile(code, "tools/build_index.py", "exec"), ns)
