"""提交前查：这一趟新增或改动的页面里，有没有把图片、声音转成 Base64 塞进网页。

    python3 tools/check_media.py        # Windows：py -3.13 tools/check_media.py

查哪些：跟 check_privacy.py 默认模式同一个范围（直接调它的 versions()，范围改一处两边一起变）——
工作区、暂存区里改了的，还没跟踪的新文件，origin/main 之后每个提交里改过的；只看 .html、.htm、.svg。
没动过的老页不追查；店里还剩哪些胖页，用 `python3 tools/unbox_media.py --find` 列。
本地的 origin/main 旧了会把别人早推上去的页也算进来，报的是没动过的页就先 fetch（见 tools/手册/git.md）。

认法直接用 unbox_media.py 的 find_payloads，跟 --find 一个标准：data: 网址、不带 data: 头的盒子
（<script type="application/octet-stream"> 之类）、拼起来的长串 Base64 数组、裸的长 Base64 字符串，
按解出来的文件开头认得出是图片、声音的才算；SVG 里的 C2PA 签名、字体这些不算。

一页里这些乱码加起来到 LIMIT（8 KB，按页面里 Base64 的字数算，跟 --find 的「乱码量」同一个数）就拦。
依据，2026-11-25 用 find_payloads 量的、留着不拆的极小件：
  grok/哄睡/嘟嘟机.html                    一段 wav 提示音，3588 字（最大的一个）
  claude/小科普/momoyu造型宪法.html          两张 png 小图标，共 2352 字，最长一段 1188
  claude/小科普/狐狸和暹罗的定妆照三.html      同上，共 2352 字
8 KB 比嘟嘟机还多留四 KB 多。再往上，店里最小的一张正经图是 claude/博物馆/写错了一笔.html 的 png，
15660 字，那已经是该拆的了。

拦住了就先用 tools/unbox_media.py 把图片、声音拆进页面旁边的同名文件夹（做法见 tools/手册/新页面.md
「图片和声音放哪」），再提交。查出问题退出码是 1，读不到 Git 数据是 2。
"""
import collections
import hashlib
from pathlib import Path
import subprocess
import sys

import check_privacy
import unbox_media

LIMIT = 8 * 1024          # 依据见开头：留着不拆的极小件最大是嘟嘟机的 3588 字，往上留了四 KB 多
PAGES = ('.html', '.htm', '.svg')


def check(root):
    seen, count = set(), 0
    for path, source, data in check_privacy.versions(root, False):
        if data is None or not path.lower().endswith(PAGES):
            continue
        fingerprint = (path, hashlib.sha256(data).digest())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        media = [p for p in unbox_media.find_payloads(data) if p.cat == 'media']
        total = sum(p.body[1] - p.body[0] for p in media)
        if total < LIMIT:
            continue
        big = max(media, key=lambda p: p.body[1] - p.body[0])
        fmts = '、'.join(f'{f}×{n}' for f, n in collections.Counter(p.fmt for p in media).most_common())
        print(f'{path} [{source}]：图片、声音的 Base64 共 {unbox_media.human(total)}'
              f'（{len(media)} 段，{fmts}；最长一段在第 {big.line} 行，'
              f'{unbox_media.human(big.body[1] - big.body[0])}）')
        count += 1
    if count:
        print(f'图片声音检查未通过：上面 {count} 处的页面肚子里塞着图片、声音（一页到 '
              f'{unbox_media.human(LIMIT)} 就拦）。先用 tools/unbox_media.py 拆进同名文件夹，'
              f'做法见 tools/手册/新页面.md「图片和声音放哪」。')
        print('报的要是没动过的页、别人早推上去的提交，多半是本地 origin/main 旧了：'
              '先 git fetch origin main 再跑（见 tools/手册/git.md）。')
        return 1
    print('图片声音检查通过')
    return 0


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='backslashreplace')
    try:
        root = Path(check_privacy.git(Path(__file__).resolve().parent,
                                      'rev-parse', '--show-toplevel').decode('utf-8').strip())
        return check(root)
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        print('图片声音检查未完成：读不到 Git 数据或文件（默认要有 origin/main）。', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
