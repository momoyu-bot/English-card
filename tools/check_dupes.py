"""找内容一模一样的页面（导入/上传一批之后跑，做完新页提交前也跑）。

比之前先把 CRLF / CR 统一成 LF：同一份内容换一种行尾，
肉眼一样、指纹却不同，直接比会漏掉大半。
还没 git add 的新页也算进来（以前只看已跟踪的，刚做好的新页会被漏掉）。
查出重复时退出码是 1。

    python3 tools/check_dupes.py
"""
import collections
import hashlib
import subprocess
import sys

G = ['git', '-c', 'core.quotepath=false']


def ls(*args):
    # -z 加按 UTF-8 解：中文文件名在哪台电脑上都原样拿到，不随系统编码变。
    out = subprocess.run(G + ['ls-files', '-z', *args], capture_output=True, check=True).stdout
    return {f for f in out.decode('utf-8').split('\0') if f}


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='backslashreplace')
files = sorted(ls('--cached', '--others', '--exclude-standard', '*.html', '*.svg') - ls('--deleted'))
seen = collections.defaultdict(list)
for f in files:
    b = open(f, 'rb').read().replace(b'\r\n', b'\n').replace(b'\r', b'\n').strip()
    seen[hashlib.md5(b).hexdigest()].append(f)
hit = [v for v in seen.values() if len(v) > 1]
for v in hit:
    print('重复:', *v, sep='\n  ')
print(f'查了 {len(files)} 个文件，{len(hit)} 组重复。')
sys.exit(1 if hit else 0)
