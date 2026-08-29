#!/usr/bin/env python3
"""临时：从 index.html 扣掉 gpt 门牌。下一步把真生成器放回来。"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")

def main():
    src = open(INDEX, encoding="utf-8").read()
    new = re.sub(
        r'\n  <details class="group"[^>]*>\s*<summary class="tag">gpt</summary>[\s\S]*?</details>(?=\n  <details class="group")',
        '',
        src,
        count=1,
    )
    if "--check" in sys.argv:
        if new != src:
            print("index.html 还挂着 gpt 灯牌", file=sys.stderr)
            return 1
        print("index.html 已经没有 gpt 灯牌")
        return 0
    if new == src:
        print("index.html 无变化（没有 gpt 灯牌，或模式没匹上）")
        return 0
    open(INDEX, "w", encoding="utf-8").write(new)
    print("index.html 已撤掉 gpt 灯牌")
    return 0

if __name__ == "__main__":
    sys.exit(main())
