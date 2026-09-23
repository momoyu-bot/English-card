"""拿每个页面的首版跟现在比，列出被改过的中文字。

用常用字的错字（砰→磅、蜷→踩）字频扫描看不见，这个看得见：
这类错几乎都是后来有人动文件时种进去的，不是进店时就带的。

    python3 tools/scan_vs_first.py            # 全仓库，几分钟
    python3 tools/scan_vs_first.py claude/哄睡  # 只扫某个目录

要完整历史：浅克隆先 git fetch --unshallow origin main。
输出分三类看，只有「改坏了」该动：改坏了 / 原件自带错字后来被修好 / 整页重写。
"""
import difflib
import re
import subprocess
import sys

G = ['git', '-c', 'core.quotepath=false']   # 少了这个，中文名的文件会被静默跳过
args = sys.argv[1:]
files = [f for f in subprocess.run(G + ['ls-files', '--'] + args, capture_output=True, text=True)
         .stdout.split('\n') if re.search(r'\.(html|svg)$', f) and f != 'index.html']
CJK = re.compile(r'[一-鿿]')
SKIP = re.compile(r'<title>|name="description"|<desc\b')
for f in files:
    out = subprocess.run(G + ['log', '--follow', '--name-only', '--format=@@%H',
                              '--diff-filter=A', '--', f], capture_output=True, text=True).stdout.split('\n')
    revs = [(l[2:].strip(), next((out[j].strip() for j in range(i + 1, len(out)) if out[j].strip()), f))
            for i, l in enumerate(out) if l.startswith('@@')]
    if not revs:
        continue
    h, p_ = revs[-1]
    r = subprocess.run(G + ['show', f'{h}:{p_}'], capture_output=True)
    if r.returncode:
        continue
    o = r.stdout.decode('utf-8', 'replace').replace('\r\n', '\n').split('\n')
    c = open(f, 'rb').read().decode('utf-8', 'replace').replace('\r\n', '\n').split('\n')
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, o, c, autojunk=False).get_opcodes():
        if tag != 'replace':
            continue
        for a in o[i1:i2]:
            if not CJK.search(a) or SKIP.search(a):
                continue
            b = max(c[j1:j2] or [''], key=lambda x: difflib.SequenceMatcher(None, a, x).ratio())
            if a == b or SKIP.search(b) or difflib.SequenceMatcher(None, a, b).ratio() < 0.75:
                continue
            for t, x1, x2, y1, y2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
                if t == 'replace' and len(a[x1:x2]) <= 8 and CJK.search(a[x1:x2] + b[y1:y2]):
                    print(f'{f}\t{a[x1:x2]!r} -> {b[y1:y2]!r}\t…{b[max(0, y1 - 24):y2 + 24].strip()}…')
