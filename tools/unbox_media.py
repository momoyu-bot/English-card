#!/usr/bin/env python3
"""拆箱：把塞进网页的图片、声音（Base64 乱码）搬进页面旁边的同名文件夹，页面改成按相对路径去取。

在仓库根上跑（Windows 把 python3 换成 py -3.13）。只打印摘要，从不打印乱码和整行，胖页也撑不满对话。

  python3 tools/unbox_media.py --find [--min-kb 1] [--all]
      列出店里还塞着图片、声音的页，按乱码总量从大到小排（默认只列乱码 ≥ 1 KB 的页）。认得四种：
      data: 网址、不带 data: 头的盒子（<script type="application/octet-stream"> 之类）、
      拼起来的长串 Base64 数组（['…','…'].join('')，一块再短也认）、裸的长 Base64 字符串。
      「要手改」一栏有字的页不能一键拆，先 --skel 看结构。
      不是图片声音的 Base64（像 SVG 里的 C2PA 签名）默认不列，--all 才列。

  python3 tools/unbox_media.py --skel 页面.html [-o 骨架.txt]
      生成骨架：每段乱码换成「〔媒体#3 webp 412KB 1a2b3c4d〕」（最后是 sha256 前 8 位），
      每行开头标原文件的行号，太长的行截断。默认写到系统临时目录的 unbox-skel/页面名.txt
      （云端是 /tmp/unbox-skel/），不许写进仓库。看结构只读骨架，别读原页。

  python3 tools/unbox_media.py 页面.html [--dry-run] [--name 3=peach ...] [--anyway]
      一键拆「只换地址」的页：data: 网址写在 src、data-src、href、CSS 或 JS 字符串里，页面不自己解码。
      每段按文件开头的真实格式定后缀（不信 data: 里写的类型），写进同名文件夹，同一份只存一个；
      再把 data: 网址换成相对路径（中文照写），然后核对：读回的每个文件 sha256 等于原来那段解出来的结果、
      文件数对上、新页面扫不到长串 Base64、把两边的媒体换成同一个记号后其余一个字节都没变。都对上才写页面。
      文件名：有现成名字就用——JS 对象的键名 > 变量名 > 元素 id（<source> 用外层 audio/video 的 id，
      盒子 id 去掉 media-）；同一个名字落在几份不同的媒体上就不用它。键名是每件都有的字段名
      （像 GIF 馆的 gif、poster）时，用所在对象的 id 拼：pond.gif、pond-poster.png。
      没名字的按出现顺序 01.jpg、02.jpg……。--dry-run 只列清单不写；--name 编号=名字 改名（编号看清单的 #）。
      页面里有 atob、读 octet-stream 盒子、拼 data URL、split(',')[1]、'data:' 字样、<base> 这类
      要手改的地方，只列位置，不改，而且默认整页不动。看过确认要拆就加 --anyway：照样换掉能换的 data: 网址，
      盒子、数组、裸字符串里的媒体也写成文件（页面里那几段原样留着），剩下的自己手改，改完跑 --verify。
      SVG、字体、认不出的格式不拆（文件夹里不许有 .svg；字体文件不许进仓库），原地留着、列出来。

  python3 tools/unbox_media.py --verify 页面.html --against 提交号 [--code-changed]
      拆完对照：拿那笔提交里的原页（只在内存里解，不打印）跟现在的页面、文件夹比——原页每段媒体都有
      sha256 相同的文件、文件夹里没有多余文件、没有 .html/.svg、新页面扫不到长串 Base64、
      新页面引用的文件都在、每个文件都被引用到。最后把两边的媒体都换成同一个记号比剩下的字：
      一样就是「只换了地址」；手改过的页加 --code-changed，列出改了哪几处（每处只打印几十个字）。

退出码：0 全对上；1 核对没过；2 没动手（有要手改的地方、文件夹里有别的东西等，看打印的原因）。
"""
import argparse
import base64
import binascii
import bisect
import collections
import difflib
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse

G = ['git', '-c', 'core.quotepath=false']
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 认得出来就搬的格式（按文件开头的字节认，见 sniff）。SVG、字体、认不出的不搬。
MEDIA = {'gif', 'png', 'jpg', 'webp', 'avif', 'heic', 'bmp', 'ico',
         'mp3', 'aac', 'm4a', 'mp4', 'mov', 'wav', 'ogg', 'webm', 'flac'}
# 当名字太空泛、不算「现成名字」的键名和变量名（元素 id 不受这张表管）。
GENERIC = {'src', 'href', 'url', 'uri', 'data', 'dataurl', 'datauri', 'b64', 'base64',
           'value', 'content', 'source', 'file', 'raw', 'str', 's', 'b', 'd', 'x'}
SHORT_LIMIT = 200          # 不带 data: 头的乱码，连续这么多个 Base64 字符才算（防误认长单词、路径）
WS = b' \t\r\n\f\v'
QUOTES = b'"\'`'

DATA_URL = re.compile(
    rb'(?<![\w-])data:([a-z0-9.+-]+/[a-z0-9.+-]+)?'
    rb'((?:;[a-z0-9._+-]+(?:=[^;,\s"\'`()<>]*)?)*?);base64,', re.I)
# 一段乱码里的零件：Base64 字符（= 补齐就到头了）、JSON 转义的 \/、行尾续行、\n 之类的转义、
# 按编码写的一个字（\u0041、\x41，见 scan）、空白。
TOK = re.compile(rb'[A-Za-z0-9+/]+=*|\\/|\\\r\n|\\[\r\n]|\\[nrtf]|\\u[0-9A-Fa-f]{4}|\\x[0-9A-Fa-f]{2}'
                 rb'|[ \t\f\v]+|[\r\n]+')
B64_CHARS = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
LONG_CHUNK = re.compile(rb'[A-Za-z0-9+/]{%d,}=*' % SHORT_LIMIT)
# 数组里每块可能很短（一行一块），所以另认「'…块','…块'」这种接缝
JOIN_POINT = re.compile(rb'[A-Za-z0-9+/]{16}(["\'`])\s*[,+]\s*\1[A-Za-z0-9+/]{16}')
B64_OR_ESC = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\\')
CODE_OPEN = re.compile(rb'<(script|style)\b([^>]*)>', re.I)
SCRIPT_END = re.compile(rb'</script', re.I)
STYLE_END = re.compile(rb'</style', re.I)
TYPE_ATTR = re.compile(rb'\btype\s*=\s*["\']?([^"\'\s>]*)', re.I)
ID_ATTR = re.compile(rb'(?<![\w:-])id\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>"\']+))', re.I)
JS_TYPES = {b'', b'text/javascript', b'application/javascript', b'module',
            b'text/ecmascript', b'application/ecmascript', b'application/json',
            b'importmap', b'application/ld+json', b'text/babel'}
KEY_BEFORE = re.compile(
    rb'(?:([A-Za-z_$][\w$]*)|"([^"\\\r\n]{1,60})"|\'([^\'\\\r\n]{1,60})\')\s*:\s*$')
VAR_BEFORE = re.compile(rb'([A-Za-z_$][\w$]*)\s*=\s*$')

# 要手改的地方：照样换地址会坏，或者坏不坏得看代码。默认见到就整页不动。
BLOCKING = (
    (re.compile(rb'\batob\s*\('), 'atob 现场解码'),
    (re.compile(rb'application/octet-stream', re.I), 'octet-stream（盒子或类型）'),
    (re.compile(rb';base64,\s*["\'`)]'), '拼 data URL（;base64, 后面直接是引号）'),
    (re.compile(rb'data:[^"\'`\s]{0,60}\$\{'), '拼 data URL（模板字符串）'),
    (re.compile(rb'["\'`]data:["\'`;]'), "'data:' 字样（判断或拼接 data URL）"),
    (re.compile(rb'\.split\(\s*["\'],["\']\s*\)\s*\[\s*1\s*\]'), "split(',')[1]（剥 data URL 的头）"),
    (re.compile(rb'<base\b', re.I), '<base> 标签（相对路径会按它算）'),
)
# 只是留意：多半没事，拆完验的时候看一眼。
NOTICE = (
    (re.compile(rb'readAsDataURL|toDataURL|FileReader'), '读写 data URL（多半是导入导出）'),
    (re.compile(rb'getImageData'), '读画布像素（file:// 下会被拦，http 下没事）'),
    (re.compile(rb'outerHTML|XMLSerializer'), '整页导出？（导出的页会带相对路径）'),
)


def out(*a):
    print(*a, flush=True)


def human(n):
    if n >= 1048576:
        return f'{n / 1048576:.1f}MB'
    if n >= 1024:
        return f'{round(n / 1024)}KB'
    return f'{n}B'


def sniff(b):
    """按文件开头的字节认格式，认不出返回 None。"""
    if b[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return 'png'
    if b[:3] == b'\xff\xd8\xff':
        return 'jpg'
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        return 'webp'
    if b[:4] == b'RIFF' and b[8:12] == b'WAVE':
        return 'wav'
    if b[:3] == b'ID3':
        return 'mp3'
    if len(b) > 2 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0:
        return 'aac' if (b[1] >> 1) & 3 == 0 else 'mp3'      # 层号 0 是 ADTS（AAC），其余是 MPEG 音频
    if b[4:8] == b'ftyp':
        brand = b[8:12]
        if brand in (b'avif', b'avis'):
            return 'avif'
        if brand in (b'heic', b'heix', b'mif1', b'msf1'):
            return 'heic'
        if brand == b'qt  ':
            return 'mov'
        if brand in (b'M4A ', b'M4B ', b'M4P '):
            return 'm4a'
        return 'mp4' if re.search(rb'hdlr.{8}vide', b[:4 << 20], re.S) else 'm4a'
    if b[:4] == b'OggS':
        return 'ogg'
    if b[:4] == b'\x1a\x45\xdf\xa3':
        return 'webm'
    if b[:4] == b'fLaC':
        return 'flac'
    if b[:4] in (b'wOFF', b'wOF2', b'OTTO', b'\x00\x01\x00\x00', b'true', b'ttcf'):
        return 'font'
    if b[:4] == b'\x00\x00\x01\x00':
        return 'ico'
    if b[:2] == b'BM' and len(b) > 26 and int.from_bytes(b[2:6], 'little') == len(b):
        return 'bmp'
    head = b[:2048].lstrip(b'\xef\xbb\xbf' + WS)
    if head.startswith(b'<svg') or (head.startswith(b'<?xml') and b'<svg' in head):
        return 'svg'
    return None


def decode(b64):
    """照浏览器的宽松解法：末尾的 = 可有可无；中间有 =、长度除 4 余 1 就算解不开。"""
    core = b64.rstrip(b'=')
    if not core or b'=' in core or len(core) % 4 == 1:
        return None
    try:
        return base64.b64decode(core + b'=' * (-len(core) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None


def scan(s, i, mode, join=None):
    """从 i 起吃掉一段 Base64，返回 (最后一个 Base64 字符之后的位置, 拼好的 Base64)。

    mode：'tight' 中间不许夹任何东西（没引号包着的 url(…)、srcset）；
          'quoted' 引号里的字符串：可夹换行、\\n 之类的转义、\\u0041 这类按编码写的字（还原了再算）；
                   夹空格只在已吃的字数是 4 的倍数时才跨过去；
          'box' 盒子：可夹任何空白，不认转义。
    join：数组里 'A','B' / 'A'+'B' 这种拼接的正则（只有数组才给）。遇到 = 补齐就停。
    """
    parts, count, end, j, n = [], 0, i, i, len(s)
    in_gap, gap_free, back = False, False, None
    while j < n:
        m = TOK.match(s, j)
        if m is None:
            if join is not None and count:
                mj = join.match(s, j)
                if mj:
                    in_gap, gap_free, j = True, True, mj.end()
                    continue
            break
        t = m.group()
        c = t[0]
        if t[:2] in (b'\\u', b'\\x'):
            # 按编码写的一个字：JSON.parse 和 JS 字符串都会把 \u0041 还原成 A，页面拿到的是完整的 Base64。
            # 老 GIF 馆的 pond、ribbon 各有一处 \u0041（正好在会拼出 AIza 的地方，大概是躲隐私检查里
            # 「Google API 密钥」那条），以前认不得、扫到这儿就停，两张动图被截短了，截短的还能解、还像 GIF。
            # 盒子、没引号的地方没有转义一说，见到就停。还原出来是空白的跟 \n 一样当空隙，别的字也停。
            code = int(t[2:], 16)
            if mode != 'quoted' or not (code in B64_CHARS or code in b' \t\n\f\r'):
                break
            if code not in B64_CHARS:
                in_gap = gap_free = True
                j = m.end()
                continue
            t, c = bytes([code]), code                       # 还原成那个字，下面照一块 Base64 算
        if t == b'\\/' or c not in b'\\ \t\f\v\r\n':        # 一块 Base64
            if in_gap:
                if mode == 'tight':
                    break
                if not gap_free and count % 4:
                    break
            piece = b'/' if t == b'\\/' else t
            back = (end, len(parts), count) if in_gap and not gap_free else None
            parts.append(piece)
            count += len(piece)
            j = end = m.end()
            in_gap = gap_free = False
            if piece.endswith(b'='):
                break
            continue
        # 夹在中间的东西
        if mode == 'tight' or (c == 0x5C and mode == 'box'):
            break
        in_gap = True
        if c == 0x5C or c in b'\r\n':
            gap_free = True
        j = m.end()
    if back and count % 4:            # 最后一块是空格后面跟的零头（像 srcset 的 1x），不算
        end, k, count = back
        del parts[k:]
    return end, b''.join(parts)


class Pay:
    """一段乱码。kind：dataurl / box / array / string / other。
    start..end 是拆的时候要换掉的那一段（dataurl 从 data: 起），body 是 Base64 本身那一段。"""
    __slots__ = ('kind', 'start', 'end', 'body', 'mime', 'data', 'fmt', 'cat', 'sha',
                 'cands', 'num', 'name', 'line')

    def __init__(self, kind, start, end, body, b64, mime=None):
        self.kind, self.start, self.end, self.body, self.mime = kind, start, end, body, mime
        self.data = decode(b64)
        f = sniff(self.data) if self.data is not None else None
        self.fmt = f or '?'
        self.cat = ('bad' if self.data is None else 'media' if f in MEDIA
                    else f if f in ('svg', 'font') else 'unknown')
        self.sha = hashlib.sha256(self.data if self.data is not None else b64).hexdigest()
        self.cands, self.num, self.name, self.line = [], 0, None, 0

    def token(self, num=True):
        if self.cat == 'bad':
            return f'〔解不开的乱码 {human(self.body[1] - self.body[0])}〕'
        head = f'媒体#{self.num} ' if num else ''
        return f'〔{head}{self.fmt} {human(len(self.data))} {self.sha[:8]}〕'


def code_ranges(s):
    """<script>、<style> 里面那几段：[(起, 止, 'js'|'css'|'data', 标签起点, 标签属性)]。"""
    rs, pos = [], 0
    while True:
        m = CODE_OPEN.search(s, pos)
        if not m:
            return rs
        tag = m.group(1).lower()
        e = (SCRIPT_END if tag == b'script' else STYLE_END).search(s, m.end())
        stop = e.start() if e else len(s)
        if tag == b'style':
            kind = 'css'
        else:
            t = TYPE_ATTR.search(m.group(2))
            kind = 'js' if (t.group(1).lower() if t else b'') in JS_TYPES else 'data'
        rs.append((m.end(), stop, kind, m.start(), m.group(2)))
        pos = e.end() if e else len(s)


def where(rs, starts, pos):
    k = bisect.bisect_right(starts, pos) - 1
    if k >= 0 and rs[k][0] <= pos < rs[k][1]:
        return rs[k]
    return None


def tag_id(tagtext):
    m = ID_ATTR.search(tagtext)
    if m:
        return (m.group(1) or m.group(2) or m.group(3)).decode('utf-8', 'replace')
    return None


OBJ_ID = re.compile(rb'["\']?\b(?:id|name|key|slug)["\']?\s*:\s*["\']([\w-]{1,40})["\']')
BRACE = re.compile(rb'[{}]')


def object_id(s, vs):
    """vs 所在的 JS/JSON 对象 {…} 里的 id（或 name、key、slug）字段，没有就 None。
    用在键名是字段名（像 gif、poster，每件展品都有）的时候：拿展品的 id 当名字。
    Base64 里没有花括号，所以往回、往后都是跳着找括号，隔着几 MB 乱码也快。"""
    depth, k = 0, vs
    while True:
        k = max(s.rfind(b'{', 0, k), s.rfind(b'}', 0, k))
        if k < 0:
            return None
        if s[k] == 0x7D:
            depth += 1
        elif depth == 0:
            break
        else:
            depth -= 1
    depth, end = 0, None
    for m in BRACE.finditer(s, k):
        depth += 1 if m.group() == b'{' else -1
        if depth == 0:
            end = m.end()
            break
    if end is None:
        return None
    body = s[k:end]
    for m in OBJ_ID.finditer(body):
        pre = body[:m.start()]
        if pre.count(b'{') - pre.count(b'}') == 1:                 # 只认这一层的，不认里面嵌套对象的
            return m.group(1).decode('utf-8', 'replace')
    return None


def name_cands(s, vs, pe, ctx):
    """值从 vs 开始（引号、[ 或 data:），乱码到 pe 结束；按上下文找现成的名字 [(优先级, 名字)]。
    键名后面可能带一个「所在对象的 id」：(1, 键名, id)，键名是字段名时用 id 拼名字。"""
    found = []
    if ctx == 'js':
        w0 = max(0, vs - 300)
        win = s[w0:vs]
        m = KEY_BEFORE.search(win)
        if m:
            key = (m.group(1) or m.group(2) or m.group(3)).decode('utf-8', 'replace')
            found.append((1, key, object_id(s, w0 + m.start())))
        else:
            m = VAR_BEFORE.search(win)
            if m:
                found.append((2, m.group(1).decode('utf-8', 'replace')))
    elif ctx == 'html':
        lt = s.rfind(b'<', max(0, vs - 5000), vs)
        if lt >= 0 and s.find(b'>', lt, vs) == -1:              # 在一个标签的属性里
            gt = s.find(b'>', pe)
            tagtext = s[lt:vs] + s[pe:gt + 1 if gt >= 0 else pe]
            tid = tag_id(tagtext)
            if tid is None and re.match(rb'<source\b', tagtext, re.I):
                outer = list(re.finditer(rb'<(?:audio|video|picture)\b[^>]*>', s[max(0, lt - 3000):lt], re.I))
                if outer:
                    tid = tag_id(outer[-1].group())
            if tid:
                found.append((3, tid))
        else:                                                    # 在元素正文里：看紧挨着的开标签
            k = vs - 1
            while k >= 0 and s[k] in WS:
                k -= 1
            if k >= 0 and s[k:k + 1] == b'>':
                lt = s.rfind(b'<', max(0, k - 3000), k)
                if lt >= 0:
                    tid = tag_id(s[lt:k + 1])
                    if tid:
                        found.append((3, tid))
    return found


def find_payloads(s):
    # tools/check_media.py（提交前的把关）也直接用它认乱码：改认法，两边一起变。
    rs = code_ranges(s)
    starts = [r[0] for r in rs]
    nl = [m.start() for m in re.finditer(rb'\n', s)]
    pays = []

    def ctx_of(pos):
        r = where(rs, starts, pos)
        return r[2] if r else 'html'

    # 1. data: 网址
    for m in DATA_URL.finditer(s):
        a = m.start()
        if pays and a < pays[-1].end:
            continue
        q = s[a - 1:a] if a else b''
        if q and q in QUOTES:
            srcset = re.search(rb'srcset\s*=\s*$', s[max(0, a - 40):a - 1], re.I)
            mode = 'tight' if srcset else 'quoted'
        else:
            mode = 'tight'
        b0 = m.end()
        e, b64 = scan(s, b0, mode)
        if e == b0:
            continue                                   # 空的：是在拼 data URL，算在要手改的地方里
        p = Pay('dataurl', a, e, (b0, e), b64, (m.group(1) or b'').decode('ascii', 'replace'))
        vs = a - 1 if q and q in QUOTES else a
        p.cands = name_cands(s, vs, e, ctx_of(a))
        pays.append(p)
    taken = [(p.start, p.end) for p in pays]

    def inside(pos):
        k = bisect.bisect_right(taken, (pos, float('inf'))) - 1
        return k >= 0 and taken[k][0] <= pos < taken[k][1]

    extra = []
    # 2. 盒子：不是 JS 的 <script> 里整段都是 Base64
    for r in rs:
        if r[2] != 'data':
            continue
        k = r[0]
        while k < r[1] and s[k] in WS:
            k += 1
        e, b64 = scan(s, k, 'box')
        if len(b64) >= 64 and not s[e:r[1]].strip(WS) and not inside(k):
            p = Pay('box', k, e, (k, e), b64)
            tid = tag_id(s[r[3]:r[0]])
            if tid:
                p.cands = [(3, tid[6:] if tid.startswith('media-') and len(tid) > 6 else tid)]
            extra.append(p)
    taken = sorted(taken + [(p.start, p.end) for p in extra])
    # 3. 剩下的：数组（一块一块拼的）、裸字符串、正文里的长串
    cands = sorted({m.start() for m in LONG_CHUNK.finditer(s)} | {m.start() for m in JOIN_POINT.finditer(s)})
    for p0 in cands:
        if inside(p0):
            continue
        k = p0                                   # 退到这一块的开头，看它是不是在引号里
        while k > 0 and s[k - 1] in B64_OR_ESC:
            k -= 1
        q = s[k - 1:k] if k else b''
        if q and q in QUOTES:
            first = k - 1                        # 这一块的开引号；再往回找同一个数组里更早的块
            while True:
                k = first - 1
                while k >= 0 and s[k] in WS:
                    k -= 1
                if k < 0 or s[k] not in b',+':
                    break
                k -= 1
                while k >= 0 and s[k] in WS:
                    k -= 1
                if k < 0 or s[k:k + 1] != q:
                    break
                k2 = k - 1
                while k2 >= 0 and s[k2] in B64_OR_ESC:
                    k2 -= 1
                if k2 < 0 or s[k2:k2 + 1] != q or k2 == k - 1:
                    break
                first = k2
            k = first - 1
            while k >= 0 and s[k] in WS:
                k -= 1
            is_array = k >= 0 and s[k:k + 1] == b'['
            join = re.compile(re.escape(q) + rb'\s*[,+]\s*' + re.escape(q))
            e, b64 = scan(s, first + 1, 'quoted', join)
            kind, vs, b0 = ('array' if is_array else 'string'), (k if is_array else first), first + 1
        else:
            e, b64 = scan(s, p0, 'quoted')
            kind, vs, b0 = 'other', p0, p0
        if e <= p0 or len(b64) < SHORT_LIMIT:
            continue
        p = Pay(kind, b0, e, (b0, e), b64)
        p.cands = name_cands(s, vs, e, ctx_of(p0))
        extra.append(p)
        taken = sorted(taken + [(b0, e)])
    pays = sorted(pays + extra, key=lambda p: p.start)
    # 编号：同一份内容（sha256 相同）一个号，按第一次出现的先后
    nums = {}
    for p in pays:
        p.num = nums.setdefault(p.sha, len(nums) + 1)
        p.line = bisect.bisect_right(nl, p.start) + 1
    return pays


def spots(s, pays):
    """要手改的地方和要留意的地方：[(行, 说明, 前后文)]。"""
    nl = [m.start() for m in re.finditer(rb'\n', s)]
    found = ([], [])
    for i, table in enumerate((BLOCKING, NOTICE)):
        for rx, what in table:
            for m in rx.finditer(s):
                found[i].append((bisect.bisect_right(nl, m.start()) + 1, what, context(s, m.start(), m.end(), pays)))
    for p in pays:
        if p.kind != 'dataurl' and p.cat == 'media':
            label = {'box': '盒子里的媒体（读盒子的代码要改）', 'array': '拼起来的 Base64 数组（读它的代码要改）',
                     'string': '不带 data: 头的 Base64 字符串（用它的代码要改）', 'other': '页面正文里的 Base64（用它的代码要改）'}[p.kind]
            found[0].append((p.line, label, context(s, p.start, p.end, pays)))
        elif p.cat != 'media':
            label = {'svg': 'SVG', 'font': '字体', 'unknown': '认不出的格式', 'bad': '解不开的乱码'}[p.cat]
            found[1].append((p.line, f'{label}，不拆、原地留着', context(s, p.start, p.end, pays)))
    return sorted(found[0]), sorted(found[1])


def context(s, a, b, pays, w=50):
    """a..b 前后各 w 个字，乱码一律换成记号，换行显示成 ⏎。"""
    def cut(x, y):
        parts, pos = [], x
        for p in pays:
            if p.end <= x or p.start >= y:
                continue
            ps, pe = max(p.start, x), min(p.end, y)
            parts.append(s[pos:ps].decode('utf-8', 'replace'))
            parts.append('〔乱码〕')
            pos = pe
        parts.append(s[pos:y].decode('utf-8', 'replace'))
        t = ''.join(parts)
        return re.sub(r'[A-Za-z0-9+/]{40,}=*', '〔乱码〕', t).replace('\r', '').replace('\n', '⏎')
    left = cut(max(0, a - w * 3), a)[-w:]
    mid = cut(a, b)
    if len(mid) > 80:
        mid = mid[:40] + '…' + mid[-30:]
    return left + '【' + mid + '】' + cut(b, min(len(s), b + w * 3))[:w]


def pick_names(pays, overrides):
    """每份不同的媒体定一个文件名（带后缀），返回 {sha256: 文件名}。只给能搬的（cat == 'media'）起名。"""
    media = {}
    for p in pays:
        if p.cat == 'media':
            media.setdefault(p.sha, []).append(p)
    def options(p):
        """这一处的候选名 [(优先级, 名字)]：键名是字段名（多份媒体共用，或太空泛）时，换成「对象 id」或「对象 id-键名」。"""
        res = []
        for c in p.cands:
            prio, n = c[0], c[1]
            oid = c[2] if len(c) > 2 else None
            if prio == 1 and oid and (len(key_owners[n.lower()]) > 1 or n.lower() in GENERIC):
                plain = n.lower() == p.fmt or n.lower() in GENERIC
                res.append((1, oid if plain else f'{oid}-{n}'))
            res.append((prio, n))
        return res

    key_owners = collections.defaultdict(set)
    for sha, ps in media.items():
        for p in ps:
            for c in p.cands:
                key_owners[c[1].lower()].add(sha)
    owners = collections.defaultdict(set)
    for sha, ps in media.items():
        for p in ps:
            for prio, n in options(p):
                owners[n.lower()].add(sha)
    chosen, used = {}, set()
    for sha, ps in sorted(media.items(), key=lambda kv: kv[1][0].start):
        best = None
        num = ps[0].num
        if num in overrides:
            best = overrides[num]
        else:
            for prio, n in sorted((o for p in ps for o in options(p)), key=lambda x: x[0]):
                if prio < 3 and n.lower() in GENERIC:
                    continue
                if len(owners[n.lower()]) > 1:
                    continue                      # 同一个名字落在几份不同的媒体上：是字段名，不是这一件的名字
                if re.fullmatch(r'[\w-]{1,40}', n):
                    best = n
                    break
        chosen[sha] = best
    unnamed = [sha for sha in chosen if chosen[sha] is None]
    width = max(2, len(str(len(unnamed))))
    k = 0
    for sha in chosen:
        if chosen[sha] is None:
            k += 1
            chosen[sha] = str(k).zfill(width)
    final = {}
    for sha, base in chosen.items():
        ext = media[sha][0].fmt
        name, i = f'{base}.{ext}', 2
        while name.lower() in used:
            name, i = f'{base}-{i}.{ext}', i + 1
        used.add(name.lower())
        final[sha] = name
        for p in media[sha]:
            p.name = name
    return final


def pct(path):
    """相对路径里中文照写，只把会弄坏 HTML、CSS、JS 的 ASCII 符号转成 %xx。"""
    keep = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._~/-')
    return ''.join(ch if ord(ch) > 127 or ch in keep else urllib.parse.quote(ch, safe='') for ch in path)


def folder_of(page):
    return os.path.splitext(page)[0]


def read(path):
    with open(path, 'rb') as fh:
        return fh.read()


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def print_table(pays):
    seen = set()
    out('  #   哪种      行号      格式  大小     sha256前8位  出现  文件名（data: 里写的类型）')
    cnt = collections.Counter(p.sha for p in pays)
    for p in pays:
        if p.sha in seen:
            continue
        seen.add(p.sha)
        kind = {'dataurl': 'data:', 'box': '盒子', 'array': '数组', 'string': '字符串', 'other': '正文'}[p.kind]
        size = human(len(p.data)) if p.data is not None else '—'
        note = p.name or {'svg': '不拆：SVG', 'font': '不拆：字体', 'unknown': '不拆：认不出', 'bad': '不拆：解不开'}.get(p.cat, '')
        mime = f'（{p.mime}）' if p.mime else ''
        out(f'  {p.num:<3} {kind:<6} L{p.line:<8} {p.fmt:<5} {size:<8} {p.sha[:8]}     ×{cnt[p.sha]:<3} {note}{mime}')


def print_spots(block, notice):
    if block:
        out(f'要手改的地方 {len(block)} 处（只列位置，不自动改）：')
        for ln, what, c in block[:60]:
            out(f'  L{ln}  {what}：{c}')
        if len(block) > 60:
            out(f'  ……还有 {len(block) - 60} 处')
    if notice:
        out(f'留意 {len(notice)} 处（多半没事，验的时候看一眼）：')
        for ln, what, c in notice[:30]:
            out(f'  L{ln}  {what}：{c}')


def tokens(s, spans):
    """把 spans [(起, 止, 记号)] 换成记号，返回整份文字（只用来比，不打印整份）。"""
    parts, pos = [], 0
    for a, b, tok in sorted(spans):
        parts.append(s[pos:a].decode('utf-8', 'surrogateescape'))
        parts.append(tok)
        pos = b
    parts.append(s[pos:].decode('utf-8', 'surrogateescape'))
    return ''.join(parts)


def orig_spans(pays):
    return [(p.start, p.end, p.token(num=False)) for p in pays]


def ref_spans(s, page, pays, files):
    """新页面里指向同名文件夹的引用 → [(起, 止, 记号, 文件名)]；文件不在的记号是〔不存在的文件 x〕。"""
    folder = os.path.basename(folder_of(page))
    prefixes = {pct(folder) + '/', folder + '/'}
    found = []
    for pre in prefixes:
        rx = re.compile(re.escape(pre.encode('utf-8')) + rb'([^"\'`()\s<>#?,;\\]+)')
        for m in rx.finditer(s):
            if any(p.start <= m.start() < p.end for p in pays):
                continue
            name = urllib.parse.unquote(m.group(1).decode('utf-8', 'replace'))
            f = files.get(name)
            if f is None:
                tok = f'〔不存在的文件 {name}〕'
            else:
                data = f
                fmt = sniff(data) or '?'
                tok = f'〔{fmt} {human(len(data))} {sha256(data)[:8]}〕'
            found.append((m.start(), m.end(), tok, name))
    uniq = {}
    for a, b, tok, name in found:
        if a not in uniq or b - a > uniq[a][1] - a:
            uniq[a] = (a, b, tok, name)
    return sorted(uniq.values())


def compare(orig_text, new_text, limit=40):
    """两份记号化后的文字逐行比，返回差异行（截短）。"""
    if orig_text == new_text:
        return []
    a, b = orig_text.split('\n'), new_text.split('\n')
    diff = []
    for line in difflib.unified_diff(a, b, '原页', '新页', n=0, lineterm=''):
        if line.startswith(('---', '+++')):
            continue
        if len(line) > 160:
            line = line[:120] + f'…（这一行共 {len(line)} 字）'
        diff.append(line)
        if len(diff) >= limit:
            diff.append('……（后面的不打印了）')
            break
    return diff


def list_folder(folder):
    files, bad = {}, []
    if os.path.isdir(folder):
        for n in sorted(os.listdir(folder)):
            p = os.path.join(folder, n)
            if os.path.isdir(p):
                bad.append(f'文件夹里还有子文件夹 {n}')
                continue
            if n.lower().endswith(('.html', '.htm', '.svg')):
                bad.append(f'文件夹里有 {n}（首页生成器会把它当新货上架，不许放）')
            files[n] = read(p)
    return files, bad


def cmd_find(min_kb, show_all):
    out_ = subprocess.run(G + ['ls-files', '-z', '--cached', '--others', '--exclude-standard',
                               '*.html', '*.htm', '*.svg'], capture_output=True, check=True, cwd=ROOT).stdout
    names = sorted({f for f in out_.decode('utf-8').split('\0') if f})
    rows, other_only = [], 0
    for f in names:
        path = os.path.join(ROOT, f)
        if not os.path.isfile(path):
            continue
        s = read(path)
        if b';base64,' not in s and not LONG_CHUNK.search(s) and not JOIN_POINT.search(s):
            continue
        pays = find_payloads(s)
        media = [p for p in pays if p.cat == 'media']
        if not media and not show_all:
            other_only += bool(pays)
            continue
        listed = pays if show_all else media
        total = sum(p.body[1] - p.body[0] for p in listed)
        if not listed or total < min_kb * 1024:
            continue
        fmts = collections.Counter(p.fmt for p in listed)
        kinds = collections.Counter(p.kind for p in media if p.kind != 'dataurl')
        block, _ = spots(s, pays)
        flags = []
        for kind, label in (('box', '盒子'), ('array', '数组'), ('string', '字符串'), ('other', '正文')):
            if kinds[kind]:
                flags.append(f'{label}{kinds[kind]}')
        for what in sorted({w for _, w, _ in block if not w.startswith(('盒子', '拼起来', '不带', '页面正文'))}):
            flags.append(what.split('（')[0])
        rows.append((total, len(s), f, ', '.join(f'{n}×{k}' for k, n in fmts.most_common()), '、'.join(flags)))
    rows.sort(key=lambda r: (-r[0], r[2]))
    out('乱码量    页面大小  占比  里面是什么（去重前）          要手改           页面')
    for total, size, f, fm, fl in rows:
        out(f'{human(total):<9} {human(size):<9} {round(total * 100 / size):>3}%  {fm:<28} {fl or "—":<16} {f}')
    out(f'共 {len(rows)} 页。「要手改」是「—」的可以一键拆；有字的先 --skel 看结构，按工单手改那几处。')
    if other_only:
        out(f'另有 {other_only} 页只有认不出的 Base64（像 SVG 里的 C2PA 签名），不是图片声音，没列；加 --all 一起列。')


def cmd_skel(page, outpath):
    s = read(page)
    pays = find_payloads(s)
    pick_names(pays, {})
    if not outpath:
        outpath = os.path.join(tempfile.gettempdir(), 'unbox-skel', os.path.basename(folder_of(page)) + '.txt')
    absout = os.path.abspath(outpath)
    if absout.startswith(ROOT + os.sep):
        sys.exit('骨架别写进仓库，换个仓库外的地方（-o /tmp/…）。')
    os.makedirs(os.path.dirname(absout), exist_ok=True)
    # 逐段拼：乱码换成记号（data: 的头留着，看得出在哪），每行开头标原文件的行号
    lines, cur, line_no, pos = [], [], 1, 0
    segs = []
    for p in pays:
        segs.append((pos, p.body[0], None))
        segs.append((p.body[0], p.body[1], p.token()))
        pos = p.body[1]
    segs.append((pos, len(s), None))
    starts = [1]
    for a, b, tok in segs:
        if tok is not None:
            cur.append(tok)
            line_no += s.count(b'\n', a, b)
            continue
        chunk = s[a:b].decode('utf-8', 'replace').split('\n')
        for i, piece in enumerate(chunk):
            if i:
                lines.append(''.join(cur))
                line_no += 1
                starts.append(line_no)
                cur = []
            cur.append(piece)
    lines.append(''.join(cur))
    width = len(str(max(starts)))
    cut = 3000
    with open(absout, 'w', encoding='utf-8') as fh:
        for ln, text in zip(starts, lines):
            text = text.rstrip('\r')
            if len(text) > cut:
                text = text[:cut] + f'…〔这一行还有 {len(text) - cut} 字没印〕'
            fh.write(f'{ln:>{width}}│{text}\n')
    size = os.path.getsize(absout)
    out(f'骨架写好了：{absout}（{len(lines)} 行，{human(size)}）。原页 {human(len(s))}，乱码 {len(pays)} 段：')
    print_table(pays)
    print_spots(*spots(s, pays))


def cmd_unbox(page, dry, overrides, anyway):
    s = read(page)
    pays = find_payloads(s)
    if not pays:
        out('这一页没有塞着的乱码，不用拆。')
        return 0
    final = pick_names(pays, overrides)
    block, notice = spots(s, pays)
    out(f'{page}：{human(len(s))}，乱码 {len(pays)} 段，其中能搬的媒体 {len(final)} 份（去重后）。')
    print_table(pays)
    print_spots(block, notice)
    if not final:
        out('没有要搬的图片、声音（剩下的不拆），页面没动。')
        return 0
    if block and not anyway:
        out('有要手改的地方，整页没动。看过骨架、确认要拆就加 --anyway（能换的照样换，手改的自己来）。')
        return 2
    folder = folder_of(page)
    rel = os.path.basename(folder)
    swap = [p for p in pays if p.kind == 'dataurl' and p.cat == 'media']
    files = {final[p.sha]: p.data for p in pays if p.cat == 'media' and (anyway or p.kind == 'dataurl')}
    kept = [p for p in pays if p.cat != 'media']
    if kept:
        out(f'原地留着、不拆的 {len(kept)} 段：' + '、'.join(sorted({f"#{p.num} {p.fmt}" for p in kept})))
    if dry:
        out(f'（--dry-run）会写 {len(files)} 个文件到 {folder}/，换掉 {len(swap)} 处 data: 网址。什么都没写。')
        return 0
    existing, bad = list_folder(folder)
    if bad:
        out('\n'.join(bad))
        return 2
    strangers = [n for n in existing if n not in files]
    if strangers:
        out(f'{folder}/ 里已经有别的文件：{"、".join(strangers[:10])}。先看看是谁的，再拆。')
        return 2
    for n, data in files.items():
        if n in existing and sha256(existing[n]) != sha256(data):
            out(f'{folder}/{n} 已经存在、内容不一样。先看看是谁的，再拆。')
            return 2
    # 写文件，读回来核对
    os.makedirs(folder, exist_ok=True)
    for n, data in files.items():
        if n not in existing:
            with open(os.path.join(folder, n), 'xb') as fh:
                fh.write(data)
    back, _ = list_folder(folder)
    want = {sha for sha in (sha256(d) for d in files.values())}
    got = {sha256(d) for d in back.values()}
    if want != got or len(back) != len(files):
        out('写进文件夹的跟要写的对不上，页面没动。')
        return 1
    # 换引用
    parts, pos = [], 0
    for p in swap:
        parts.append(s[pos:p.start])
        parts.append(pct(f'{rel}/{p.name}').encode('utf-8'))
        pos = p.end
    parts.append(s[pos:])
    new = b''.join(parts)
    ok, report = check(page, s, new, back, allow_code=False, pending=anyway)
    for line in report:
        out(line)
    if not ok:
        out('核对没过，页面没写（文件夹里的文件已经写了，查完再决定留不留）。')
        return 1
    if not swap:
        out(f'页面里没有能直接换的 data: 网址，页面没动；{folder}/ 写好了 {len(back)} 个文件。'
            f'接着照上面列的位置手改，改完跑 --verify。')
        return 0
    with open(page, 'wb') as fh:
        fh.write(new)
    out(f'拆好了：{page} {human(len(s))} → {human(len(new))}；{folder}/ {len(back)} 个文件，'
        f'共 {human(sum(len(d) for d in back.values()))}。')
    return 0


def check(page, orig, new, files, allow_code, pending=False):
    """核对原页、新页、文件夹，返回 (全对上没有, 要打印的几行)。
    allow_code：除换地址外的改动只列出来、不算错（手改过的页）；
    pending：盒子、数组还留在页面里、文件还没被引用，不算错（--anyway 刚拆完、还没手改的时候）。"""
    rep, ok = [], True
    o = find_payloads(orig)
    n = find_payloads(new)
    fsha = {sha256(d): name for name, d in files.items()}
    media = {p.sha: p for p in o if p.cat == 'media'}
    kept_o = collections.Counter(p.sha for p in o if p.cat != 'media')
    left_media = [p for p in n if p.cat == 'media' and p.sha in media and p.sha not in fsha]
    moved = {sha for sha in media if sha in fsha}
    stay = {p.sha for p in n if p.cat == 'media'}            # 还留在页面里的媒体（--anyway 时的盒子、数组）
    missing = [sha for sha in media if sha not in fsha and sha not in stay]
    extra = [name for sha, name in fsha.items() if sha not in media]
    occ = collections.Counter(p.sha for p in o if p.cat == 'media')
    rep.append(f'原页能搬的媒体 {sum(occ.values())} 处、去重后 {len(media)} 份：' +
               ', '.join(f'{k} {v}' for k, v in collections.Counter(p.fmt for p in media.values()).most_common()) +
               f'；文件夹里 {len(files)} 个文件，sha256 对上 {len(moved)} 个。')
    if missing:
        ok = False
        rep.append(f'× 原页有 {len(missing)} 份媒体在文件夹里找不到同样的文件，新页面里也没有了：' +
                   '、'.join(f'#{media[s].num}' for s in missing))
    if extra:
        ok = False
        rep.append(f'× 文件夹里有 {len(extra)} 个文件对不上原页任何一段：' + '、'.join(extra[:10]))
    if left_media:
        rep.append(f'！新页面里还塞着 {len(left_media)} 段媒体，文件夹里没有：' +
                   '、'.join(f'L{p.line} {p.fmt}' for p in left_media[:10]))
        ok = False
    still = [p for p in n if p.cat == 'media' and p.sha in fsha]
    if still:
        rep.append(f'！新页面里还有 {len(still)} 段乱码跟文件夹里的文件一样（还没换成路径的，手改要接着做）：' +
                   '、'.join(f'L{p.line} {p.kind} {p.fmt}' for p in still[:10]))
        if not pending:
            ok = False
    kept_n = collections.Counter(p.sha for p in n if p.cat != 'media')
    if kept_n != kept_o:
        rep.append('！不拆的那几段（SVG、字体、认不出的）跟原页不一样了。')
        ok = False
    elif kept_o:
        rep.append(f'不拆、原地留着的 {sum(kept_o.values())} 段跟原页一样。')
    refs = ref_spans(new, page, n, files)
    bad_refs = sorted({r[3] for r in refs if r[3] not in files})
    if bad_refs:
        ok = False
        rep.append('× 新页面引用了文件夹里没有的文件：' + '、'.join(bad_refs[:10]))
    unused = sorted(set(files) - {r[3] for r in refs})
    if unused:
        rep.append(f'！文件夹里有 {len(unused)} 个文件在新页面里没找到字面上的引用（代码里拼路径的话正常）：' +
                   '、'.join(unused[:10]))
        if not (allow_code or pending):
            ok = False
    a = tokens(orig, orig_spans(o))
    b = tokens(new, [(p.start, p.end, p.token(num=False)) for p in n] + [(x, y, t) for x, y, t, _ in refs])
    diff = compare(a, b)
    if not diff:
        rep.append('✓ 把两边的媒体换成同一个记号后，其余一个字节都没变：只换了地址。')
    else:
        rep.append(f'{"！" if allow_code else "×"} 除了换地址，还有别的改动（{sum(1 for d in diff if d[:1] in "+-")} 行，'
                   f'行号是记号化后的，不是原文件的）：')
        rep.extend('    ' + d for d in diff)
        if not allow_code:
            ok = False
    return ok, rep


def cmd_verify(page, rev, allow_code):
    rel = os.path.relpath(os.path.abspath(page), ROOT).replace(os.sep, '/')
    r = subprocess.run(G + ['show', f'{rev}:{rel}'], capture_output=True, cwd=ROOT)
    if r.returncode:
        out(f'取不到 {rev} 里的 {rel}：' + r.stderr.decode('utf-8', 'replace').strip()[:200])
        return 2
    orig, new = r.stdout, read(page)
    files, bad = list_folder(folder_of(page))
    ok, report = check(page, orig, new, files, allow_code)
    out(f'{page}：原页（{rev}）{human(len(orig))} → 现在 {human(len(new))}；'
        f'{folder_of(page)}/ {len(files)} 个文件，共 {human(sum(len(d) for d in files.values()))}。')
    for line in bad:
        out('× ' + line)
    for line in report:
        out(line)
    ok = ok and not bad
    out('全对上了。' if ok else '没全对上，看上面打 × 和 ！ 的。')
    return 0 if ok else 1


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='backslashreplace')
    ap = argparse.ArgumentParser(description='拆箱：把塞进网页的图片、声音搬进同名文件夹。用法见文件开头。')
    ap.add_argument('page', nargs='?', help='要拆、要看骨架或要核对的页面')
    ap.add_argument('--find', action='store_true', help='列出店里还塞着图片、声音的页')
    ap.add_argument('--min-kb', type=float, default=1, help='--find 只列乱码不少于这么多 KB 的页（默认 1）')
    ap.add_argument('--all', action='store_true', help='--find 连不是图片声音的 Base64 也列')
    ap.add_argument('--skel', action='store_true', help='生成骨架')
    ap.add_argument('-o', dest='out', help='骨架写到哪（默认临时目录的 unbox-skel/）')
    ap.add_argument('--dry-run', action='store_true', help='只列清单，不写')
    ap.add_argument('--name', action='append', default=[], metavar='编号=名字', help='给第几号媒体改名')
    ap.add_argument('--anyway', action='store_true', help='有要手改的地方也照样换能换的')
    ap.add_argument('--verify', action='store_true', help='拆完对照')
    ap.add_argument('--against', help='--verify 拿哪笔提交里的原页比')
    ap.add_argument('--code-changed', action='store_true', help='--verify：手改过代码的页，差异只列出来不算错')
    a = ap.parse_args()
    if a.find:
        return cmd_find(a.min_kb, a.all) or 0
    if not a.page:
        ap.error('要给一个页面（或者用 --find）')
    if not os.path.isfile(a.page):
        ap.error(f'找不到 {a.page}')
    if a.skel:
        return cmd_skel(a.page, a.out) or 0
    if a.verify:
        if not a.against:
            ap.error('--verify 要配 --against 提交号')
        return cmd_verify(a.page, a.against, a.code_changed)
    overrides = {}
    for item in a.name:
        k, _, v = item.partition('=')
        if not k.isdigit() or not re.fullmatch(r'[\w-]{1,40}', v):
            ap.error(f'--name 写成 编号=名字（名字只用字母、数字、汉字、- 和 _）：{item}')
        overrides[int(k)] = v
    return cmd_unbox(a.page, a.dry_run, overrides, a.anyway)


if __name__ == '__main__':
    sys.exit(main())
