#!/usr/bin/env python3
"""
重新生成 index.html 里的页面清单。

首页不再在打开时去问 GitHub 有哪些网页——清单在这里生成好，
直接写进 index.html。所以断网能看、GitHub 挂了能看、也不受
匿名接口每小时 60 次的限制。

用法：  python3 tools/build_index.py          # 写入 index.html
        python3 tools/build_index.py --check  # 只检查是否需要重新生成

这个脚本由 .github/workflows/build-index.yml 在每次 push 后自动跑，
不需要任何人记得手动执行。
"""
