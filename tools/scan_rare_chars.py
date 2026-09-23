"""按字频捞可疑错别字：错字多半是全仓库只出现一两次的冷僻字。

    python3 tools/scan_rare_chars.py

捞出来的要人工看上下文，生僻不等于错。
抓不到「用常用字的错字」，那一类用 tools/scan_vs_first.py。
"""
import collections
import io
import re
import subprocess

G = ['git', '-c', 'core.quotepath=false']
# CLAUDE.md 自己列着一堆错字样本，扫进来全是噪音
files = [f for f in subprocess.run(G + ['ls-files', '*.html', '*.svg', '*.md'],
         capture_output=True, text=True).stdout.split('\n') if f and f != 'CLAUDE.md']


def tier(ch):
    """GB2312 一级字库=最常用的 3755 字，二级=次常用，装不下的=生僻"""
    try:
        return 1 if ch.encode('gb2312')[0] <= 0xD7 else 2
    except UnicodeEncodeError:
        return 3


freq, where = collections.Counter(), collections.defaultdict(list)
for f in files:
    s = io.open(f, encoding='utf-8', errors='replace').read()
    for ch in re.findall(r'[一-鿿]', s):
        freq[ch] += 1
        if len(where[ch]) < 2 and f not in where[ch]:
            where[ch].append(f)

print('=== GB2312 都装不下的（最可疑）===')
for c, n in sorted([(c, n) for c, n in freq.items() if tier(c) == 3], key=lambda x: x[1]):
    print(f'  {c} x{n}  {where[c][0]}')
print('=== 二级字库且出现 <=5 次 ===')
print('  ' + ' '.join(f'{c}({n})' for c, n in
      sorted([(c, n) for c, n in freq.items() if tier(c) == 2 and n <= 5], key=lambda x: x[1])))
