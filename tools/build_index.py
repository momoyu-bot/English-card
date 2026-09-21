#!/usr/bin/env python3
"""把残掉的生成器从已知完好的提交拉回来，补上「显影」，再照常跑。

2026-09-21：改 CAT_ORDER 时整份覆盖失败，tools/build_index.py 写成了残页。
首页清单没被改掉。这份短脚本只做三件事：取回完好源、补显影、生成清单。
"""
import pathlib, re, urllib.request

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parent.parent
GOOD = (
    "https://raw.githubusercontent.com/momoyu-bot/English-card/"
    "5b23b962c4282b9f02fc2ec18f5304f668664afe/tools/build_index.py"
)


def patched_source():
    with urllib.request.urlopen(GOOD, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    text, n1 = re.subn(
        r'("打捞机", )("盲盒"\])',
        r'\1"显影", \2',
        text,
        count=1,
    )
    text, n2 = re.subn(
        r'("打捞机": "salvage", )("盲盒": "lucky bag",)',
        r'\1"显影": "developing",\n    \2',
        text,
        count=1,
    )
    old_skip = (
        "            for c in CAT_ORDER:\n"
        "                sub = buckets[c]\n"
        "                if not sub:\n"
        "                    continue\n"
        "                sub = sorted(sub, key=lambda e: sort_key(e[\"name\"]))\n"
        "                lines.append('    <details class=\"pack\">')\n"
        "                lines.append(f'      <summary class=\"pack-tag\">{esc(display_cat(c))}</summary>')\n"
        "                lines.append('      <ul class=\"list\">')\n"
        "                render_items(lines, sub, step, 8)\n"
        "                lines.append(\"      </ul>\")\n"
        "                lines.append(\"    </details>\")\n"
    )
    new_skip = (
        "            for c in CAT_ORDER:\n"
        "                sub = buckets[c]\n"
        "                if not sub and not os.path.isdir(os.path.join(ROOT, folder, c)):\n"
        "                    continue\n"
        "                lines.append('    <details class=\"pack\">')\n"
        "                lines.append(f'      <summary class=\"pack-tag\">{esc(display_cat(c))}</summary>')\n"
        "                if not sub:\n"
        "                    lines.append('      <p class=\"soon\">还没有页。</p>')\n"
        "                else:\n"
        "                    sub = sorted(sub, key=lambda e: sort_key(e[\"name\"]))\n"
        "                    lines.append('      <ul class=\"list\">')\n"
        "                    render_items(lines, sub, step, 8)\n"
        "                    lines.append(\"      </ul>\")\n"
        "                lines.append(\"    </details>\")\n"
    )
    if old_skip not in text:
        raise SystemExit("完好源里找不到货架渲染那段，不敢补丁")
    text = text.replace(old_skip, new_skip, 1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"补丁没打准：CAT_ORDER={n1} SHELF_EN={n2}")
    if '"显影"' not in text:
        raise SystemExit("补丁打完源里没有显影")
    return text


def main():
    text = patched_source()
    ns = {"__name__": "__main__", "__file__": str(HERE)}
    exec(compile(text, str(HERE), "exec"), ns)


if __name__ == "__main__":
    main()
