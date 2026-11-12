"""提交前的三项检查，一次跑完：重复的页、跑不起来的脚本、隐私。

    python3 tools/check.py        # Windows：py -3.13 tools/check.py

三项都过，退出码才是 0。哪一项没过，照它打印出来的去改；
想单独重查某一项，直接跑那一个脚本（各自开头写着查什么、怎么读结果）。
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = (
    ("check_dupes.py", "重复的页"),
    ("check_scripts.py", "页面里的脚本"),
    ("check_privacy.py", "隐私"),
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="backslashreplace")
failed = []
for name, what in CHECKS:
    print(f"== {what}（{name}）", flush=True)
    # 前两个脚本按仓库根来找文件，所以不管从哪儿叫它，都回到根上跑。
    if subprocess.run([sys.executable, os.path.join(HERE, name)],
                      cwd=os.path.dirname(HERE)).returncode:
        failed.append(what)
print("三项都过了。" if not failed else "没过：" + "、".join(failed))
sys.exit(1 if failed else 0)
