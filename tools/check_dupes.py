"""找内容一模一样的页面（导入/上传一批之后跑）。

比之前先把 CRLF / CR 统一成 LF：同一份内容换一种行尾，
肉眼一样、指纹却不同，直接比会漏掉大半。

    python3 tools/check_dupes.py
"""
import collections
import hashlib
import subprocess

G = ['git', '-c', 'core.quotepath=false']
files = [f for f in subprocess.run(G + ['ls-files', '*.html', '*.svg'],
         capture_output=True, text=True).stdout.split('\n') if f]
seen = collections.defaultdict(list)
for f in files:
    b = open(f, 'rb').read().replace(b'\r\n', b'\n').replace(b'\r', b'\n').strip()
    seen[hashlib.md5(b).hexdigest()].append(f)
hit = [v for v in seen.values() if len(v) > 1]
for v in hit:
    print('重复:', *v, sep='\n  ')
print(f'查了 {len(files)} 个文件，{len(hit)} 组重复。')
