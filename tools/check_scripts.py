"""把每个页面里的内联脚本交给 node 判语法，列出整段跑不起来的。

最常见的病因：字符串里的 <br> 在导入时变成了真换行，
普通引号字符串不能跨行，整段脚本一行都不执行，按钮全是死的。

    python3 tools/check_scripts.py

没输出就是干净的。需要装了 node。
"""
import io
import os
import re
import subprocess
import tempfile

G = ['git', '-c', 'core.quotepath=false']
files = [f for f in subprocess.run(G + ['ls-files', '*.html'],
         capture_output=True, text=True).stdout.split('\n') if f]
# 只查真的是 JS 的：没写 type，或者 type 明说是 javascript / module。
# text/plain（梦境的内嵌底稿）、text/babel（JSX）、application/json 都跳过，
# 否则全部误报 Unexpected token '<'。
JS_OK = re.compile(r'^(text/javascript|application/javascript|module)$', re.I)
for f in files:
    s = io.open(f, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', s):
        attrs, code = m.group(1), m.group(2)
        if re.search(r'\bsrc=', attrs) or not code.strip():
            continue
        t = re.search(r'\btype\s*=\s*["\']([^"\']+)["\']', attrs)
        if t and not JS_OK.match(t.group(1).strip()):
            continue
        base = s[:m.start(2)].count('\n') + 1          # 这段脚本在文件里的起始行
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as fh:
            fh.write(code)
            tmp = fh.name
        r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
        os.unlink(tmp)
        if r.returncode:
            err = next((l.strip() for l in r.stderr.split('\n') if 'Error' in l), '')
            ln = re.search(r'\.js:(\d+)', r.stderr)
            where = f'文件第 {base + int(ln.group(1)) - 1} 行' if ln else f'脚本起于第 {base} 行'
            print(f'{f}\t{where}\t{err[:70]}')
