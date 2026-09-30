"""把三页造型宪法里「开新对话时整段贴过去」的那段抽出来，合成 tools/小萌物画法.txt。

    python3 tools/build_huafa.py           # 重抽，有变化就写回
    python3 tools/build_huafa.py --check   # 只查合订本是不是最新的，不是就退出码 1

小萌物短片全员出场，三页整页照读，一场还没动笔就先吃掉五万多 token；
页面里写给模型的其实只有这一段，其余是给人看的舞台、按钮和来龙去脉。
合订本是抽出来的不是抄的：原页一改，push 后工作流跟着重抽，不会跟原页走样。

某一页抽不出来（改了结构、挪了位置），那一段换成一句「去翻原页」，脚本照样写完、
不报错——宁可让读的人多翻一页，也别为这个让工作流红。
要换抽哪几页、抽哪几段，改下面 SOURCES 这张表。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = 'tools/小萌物画法.txt'

# (标题, 原页, 要抽的几段)。每段是 (变量名, 往里走的键, 这段前面要不要加一行小标题)。
# 键为空 = 变量本身就是一串字符串；有键 = 变量是个 {…}，按键一层层往里找到那串字符串。
SOURCES = [
    ('Clawd', 'claude/小科普/Clawd造型宪法（Code版）.html', [
        ('ZH', (), None),
        ('DLC', ('art', 'zh'), '—— 站姿 DLC ——'),
        ('DLC', ('tuck', 'zh'), None),
    ]),
    ('小脸蛋（小粉、小紫、小黑）', 'claude/小科普/小脸蛋造型宪法（实测版） (1).html', [
        ('ZH', (), None),
    ]),
    ('momoyu（StashYu、FetchMo）', 'claude/小科普/momoyu造型宪法.html', [
        ('DATA', ('rules', 'zh'), None),
    ]),
]

HEAD = """小萌物画法（合订本）

三页造型宪法里「开新对话时整段贴过去」的那一段，按 Clawd、小脸蛋、momoyu 排在一起。
是 tools/build_huafa.py 从原页抽出来的，push 后工作流会重抽；别在这里手改，要改就改原页。
怎么用这几段，看 CLAUDE.md「Clawd、小脸蛋、momoyu 怎么画」那四句。
原页里的图、试画按钮、量法和来龙去脉这里都没搬，要用就去翻原页。
"""

ESC = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f', 'v': '\v'}


def skip_blank(src, i):
    while i < len(src) and src[i] in ' \t\r\n':
        i += 1
    return i


def read_string(src, i):
    """从 src[i] 起读一串用 + 连起来的 JS 字符串，返回 (解码后的文字, 读到哪)。"""
    out, n = [], len(src)
    while True:
        i = skip_blank(src, i)
        if i >= n or src[i] not in '\'"':
            raise ValueError('这里该是一串字，却是 %r' % src[i:i + 12])
        q, i = src[i], i + 1
        while True:
            if i >= n:
                raise ValueError('一串字没收尾')
            c = src[i]
            if c == q:
                i += 1
                break
            if c in '\r\n':
                raise ValueError('一串字中间断了行')
            if c != '\\':
                out.append(c)
                i += 1
                continue
            e = src[i + 1]
            if e in ESC:
                out.append(ESC[e])
                i += 2
            elif e == 'u' and src[i + 2] == '{':
                j = src.index('}', i)
                out.append(chr(int(src[i + 3:j], 16)))
                i = j + 1
            elif e == 'u':
                out.append(chr(int(src[i + 2:i + 6], 16)))
                i += 6
            elif e == 'x':
                out.append(chr(int(src[i + 2:i + 4], 16)))
                i += 4
            elif e in '\r\n':                       # 反斜杠续行
                i += 3 if src[i + 1:i + 3] == '\r\n' else 2
            else:                                   # \' \" \\ 之类
                out.append(e)
                i += 2
        j = skip_blank(src, i)
        if j < n and src[j] == '+':
            i = j + 1
            continue
        return ''.join(out), j


def walk(src, i, stop, on_top=None):
    """在 src[i:stop] 里走一遍，跳过字符串和注释。
    给了 on_top 时，每到对象第一层的一个位置就问它一次，它返回非 None 就停下交出结果。
    没给 on_top 时，src[i] 应是 '{'，返回和它配对的 '}' 的下标。"""
    depth, q = 0, None
    while i < stop:
        c = src[i]
        if q:
            if c == '\\':
                i += 2
                continue
            if c == q:
                q = None
            i += 1
            continue
        if on_top and depth == 1:
            got = on_top(i)
            if got is not None:
                return got
        if c in '\'"`':
            q = c
        elif src.startswith('//', i):
            i = src.find('\n', i)
            if i < 0:
                break
            continue
        elif src.startswith('/*', i):
            i = src.find('*/', i) + 2
            if i < 2:
                break
            continue
        elif c in '{[(':
            depth += 1
        elif c in '}])':
            depth -= 1
            if depth == 0 and not on_top:
                return i
        i += 1
    raise ValueError('没找到收尾的括号')


def find_key(src, start, end, key):
    """在 src[start] 那个 {…} 的第一层里找 key:，返回冒号后面的下标。"""
    pat = re.compile(r'(["\']?)%s\1\s*:' % re.escape(key))

    def here(i):
        if src[i] not in '\'"' and i and (src[i - 1].isalnum() or src[i - 1] in '_$'):
            return None
        m = pat.match(src, i)
        return m.end() if m else None
    try:
        return walk(src, start, end, here)
    except ValueError:
        raise ValueError('对象里找不到 %s' % key)


def grab(src, var, keys):
    m = re.search(r'\b(?:var|let|const)\s+%s\s*=' % re.escape(var), src)
    if not m:
        raise ValueError('页面里找不到 %s' % var)
    i = skip_blank(src, m.end())
    for k in keys:
        if src[i] != '{':
            raise ValueError('%s 不是个 {…}' % var)
        end = walk(src, i, len(src))
        i = skip_blank(src, find_key(src, i, end, k))
    return read_string(src, i)[0]


def build():
    parts, warns = [HEAD], []
    for title, page, pieces in SOURCES:
        parts.append('\n==== %s ====\n原页：%s\n' % (title, page))
        try:
            src = io.open(os.path.join(ROOT, page), encoding='utf-8').read()
            texts = []
            for var, keys, label in pieces:
                t = grab(src, var, keys).strip('\n')
                if not t.strip():
                    raise ValueError('%s 抽出来是空的' % var)
                texts.append((label + '\n\n' if label else '') + t)
            parts.append('\n' + '\n\n'.join(texts) + '\n')
        except FileNotFoundError:
            warns.append((title, '原页不在了'))
            parts.append('\n（这一段这次没抽出来：原页不在了。去 CLAUDE.md 那一节看现在该翻哪一页。）\n')
        except (ValueError, IndexError) as e:
            warns.append((title, str(e)))
            parts.append('\n（这一段这次没抽出来：%s。直接去翻上面那一页。）\n' % e)
    return ''.join(parts), warns


def main():
    text, warns = build()
    for title, why in warns:
        print('::warning::小萌物画法：%s 没抽出来（%s），合订本里这一段换成了「去翻原页」' % (title, why))
    path = os.path.join(ROOT, OUT)
    try:
        old = io.open(path, encoding='utf-8').read()
    except FileNotFoundError:
        old = None
    if '--check' in sys.argv[1:]:
        if old != text:
            print('合订本过期了：跑一遍 python3 tools/build_huafa.py')
            sys.exit(1)
        print('合订本是最新的。')
        return
    if old == text:
        print('合订本没变化。')
        return
    io.open(path, 'w', encoding='utf-8', newline='\n').write(text)
    print('写好了：%s（%d 字节）' % (OUT, len(text.encode('utf-8'))))


if __name__ == '__main__':
    main()
