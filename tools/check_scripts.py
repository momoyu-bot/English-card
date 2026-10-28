"""把每个页面里的内联脚本交给 node 判语法，列出整段跑不起来的。

最常见的病因：字符串里的 <br> 在导入时变成了真换行，
普通引号字符串不能跨行，整段脚本一行都不执行，按钮全是死的。

    python3 tools/check_scripts.py

没输出就是干净的；查出问题时退出码是 1。需要装了 node。
还没 git add 的新页也查（以前只查已跟踪的，刚做好的新页会被漏掉）。
普通脚本一次全交给同一个 node 判（以前每段起一个 node，七百多段要等十几秒，Windows 上更久）；
判法同 `node --check`：按 CommonJS 的包法编译、不执行，只是不再「当成 ES 模块再试一次」，
那种写法放在普通 <script> 里浏览器本来就报错。type="module" 的段仍逐段 `node --check`。
"""
import io
import json
import os
import re
import subprocess
import sys
import tempfile

G = ['git', '-c', 'core.quotepath=false']


def ls(*args):
    # -z 加按 UTF-8 解：中文文件名在哪台电脑上都原样拿到，不随系统编码变。
    out = subprocess.run(G + ['ls-files', '-z', *args], capture_output=True, check=True).stdout
    return {f for f in out.decode('utf-8').split('\0') if f}


def node(*args, **kw):
    try:
        return subprocess.run(['node', *args], capture_output=True, **kw)
    except FileNotFoundError:
        print('脚本检查没跑成：这台电脑找不到 node。')
        sys.exit(2)


def report(f, base, ln, err):
    where = f'文件第 {base + ln - 1} 行' if ln else f'脚本起于第 {base} 行'
    print(f'{f}\t{where}\t{err[:70]}')


if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='backslashreplace')
files = ls('--cached', '--others', '--exclude-standard', '*.html') - ls('--deleted')
# 只查真的是 JS 的：没写 type，或者 type 明说是 javascript / module。
# text/plain（梦境的内嵌底稿）、text/babel（JSX）、application/json 都跳过，
# 否则全部误报 Unexpected token '<'。
JS_OK = re.compile(r'^(text/javascript|application/javascript|module)$', re.I)
plain, modules = [], []
for f in sorted(files):
    s = io.open(f, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'<script([^>]*)>([\s\S]*?)</script>', s):
        attrs, code = m.group(1), m.group(2)
        if re.search(r'\bsrc=', attrs) or not code.strip():
            continue
        t = re.search(r'\btype\s*=\s*["\']([^"\']+)["\']', attrs)
        if t and not JS_OK.match(t.group(1).strip()):
            continue
        base = s[:m.start(2)].count('\n') + 1          # 这段脚本在文件里的起始行
        job = {'f': f, 'base': base, 'code': code}
        (modules if t and t.group(1).strip().lower() == 'module' else plain).append(job)

# 普通脚本：同一个 node 进程逐段编译，只回报编译不过的。
JS = r'''
const vm = require('vm'); let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', d => buf += d);
process.stdin.on('end', () => {
  const bad = [];
  JSON.parse(buf).forEach((code, i) => {
    try { vm.compileFunction(code, ['exports', 'require', 'module', '__filename', '__dirname'], {filename: 'x.js'}); }
    catch (e) {
      if (!(e instanceof SyntaxError)) return;
      const m = /x\.js:(\d+)/.exec(String(e.stack));
      bad.push([i, m ? +m[1] : 0, 'SyntaxError: ' + e.message]);
    }
  });
  process.stdout.write(JSON.stringify(bad));
});
'''
found = 0
if plain:
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as fh:
        fh.write(JS)
        runner = fh.name
    try:
        r = node(runner, input=json.dumps([j['code'] for j in plain]).encode('ascii'))
    finally:
        os.unlink(runner)
    if r.returncode:
        err = r.stderr.decode('utf-8', 'replace').strip().split('\n')[-1]
        print('脚本检查没跑完：node 自己报错了。', err[:100])
        sys.exit(2)
    for i, ln, err in json.loads(r.stdout.decode('utf-8') or '[]'):
        report(plain[i]['f'], plain[i]['base'], ln, err)
        found += 1

# type="module" 的段（现在店里没有）：照旧逐段 node --check。
for j in modules:
    with tempfile.NamedTemporaryFile('w', suffix='.mjs', delete=False, encoding='utf-8') as fh:
        fh.write(j['code'])
        tmp = fh.name
    r = node('--check', tmp)
    os.unlink(tmp)
    if r.returncode:
        stderr = r.stderr.decode('utf-8', 'replace')
        err = next((l.strip() for l in stderr.split('\n') if 'Error' in l), '')
        ln = re.search(r'\.mjs:(\d+)', stderr)
        report(j['f'], j['base'], int(ln.group(1)) if ln else 0, err)
        found += 1

sys.exit(1 if found else 0)
