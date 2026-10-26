"""提交前检查隐私；默认查待提交、待推送文件，--all 查全部跟踪文件。

只用标准库。按 UTF-8 读取，跳过二进制文件；不向输出复制整行内容。
默认同时检查工作区、暂存区和 origin/main 之后每个提交中的文件版本，
避免暂存内容或尚未推送的历史被后续修改掩盖。忽略的未跟踪文件不检查。
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


GIT = ("git", "-c", "core.quotepath=false")
LOCAL_PATH = re.compile(
    r"(?:[A-Z]:[\\/]+Users[\\/]+|/(?:home|Users)/+)"
    r"(?P<username>[^\\/\r\n\"'`]+)(?:[\\/]+|$)",
    re.IGNORECASE,
)
EMAIL = re.compile(
    r"(?<![A-Z0-9._%+-])[A-Z0-9_%+-][A-Z0-9.!#$%&'*+/=?^_`{|}~-]*@"
    r"(?P<domain>(?:[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?\.)+[A-Z]{2,})"
    r"(?![A-Z0-9-])",
    re.IGNORECASE,
)
ALLOWED_EMAIL_DOMAINS = {"users.noreply.github.com", "example.com"}
SECRET_RULES = (
    ("GitHub 密钥", re.compile(r"(?:ghp_|gho_|github_pat_)[A-Za-z0-9_]+")),
    ("Google API 密钥", re.compile(r"AIza[A-Za-z0-9_-]+")),
    ("Slack 密钥", re.compile(r"xox[bp]-[A-Za-z0-9-]+")),
    ("sk 密钥", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("Bearer 凭证", re.compile(r"Bearer[ \t]+[A-Za-z0-9._~+/=-]{20,}", re.I)),
    ("私钥", re.compile(r"-----BEGIN(?: [A-Z0-9]+)* PRIVATE KEY-----", re.I)),
)


def is_placeholder(value):
    value = value.strip()
    return (
        value == "~"
        or value.startswith("$")
        or any(value.startswith(left) and value.endswith(right)
               for left, right in (("<", ">"), ("%", "%"), ("{", "}")))
    )


def username_patterns():
    # 只在运行时取当前机器的名字，源文件中不保存任何真实用户名。
    names = {os.environ.get("USERNAME", ""), os.environ.get("USER", "")}
    names.add(Path(os.path.expanduser("~")).name)
    return tuple(re.compile(re.escape(name), re.IGNORECASE)
                 for name in sorted(names)
                 if name and not is_placeholder(name))


def find_hits(text, names):
    """返回位置和类别，调用方只输出遮住后的命中值。"""
    hits = []
    for match in LOCAL_PATH.finditer(text):
        if not is_placeholder(match.group("username")):
            hits.append((match.start(), match.end(), "本地用户路径"))
    for pattern in names:
        hits.extend((m.start(), m.end(), "当前用户名")
                    for m in pattern.finditer(text))
    for match in EMAIL.finditer(text):
        if (match.group("domain").casefold() not in ALLOWED_EMAIL_DOMAINS
                and match.group(0).casefold() != "noreply@anthropic.com"):
            hits.append((match.start(), match.end(), "邮箱"))
    for category, pattern in SECRET_RULES:
        hits.extend((m.start(), m.end(), category) for m in pattern.finditer(text))
    return sorted(set(hits))


def mask(value):
    if len(value) < 3:
        return "***"
    keep = min(3, max(1, len(value) // 4))
    return value[:keep] + "***" + value[-keep:]


def safe_path(path, names):
    # 文件名本身也可能带隐私；合并重叠命中后再遮住，并转义控制字符。
    spans = []
    for start, end, _ in find_hits(path, names):
        if spans and start <= spans[-1][1]:
            spans[-1] = (spans[-1][0], max(end, spans[-1][1]))
        else:
            spans.append((start, end))
    for start, end in reversed(spans):
        path = path[:start] + mask(path[start:end]) + path[end:]
    return json.dumps(path, ensure_ascii=False)


def git(root, *args):
    return subprocess.run(
        (*GIT, *args), cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, check=True,
    ).stdout


def git_paths(root, *args):
    return {os.fsdecode(name) for name in git(root, *args).split(b"\0") if name}


def read_worktree(root, path):
    target = root / path
    try:
        # 不跟随符号链接去读仓库外的文件；链接目标本身是 Git 存储的文本。
        if target.is_symlink():
            return os.fsencode(os.readlink(target))
        if target.is_dir():
            return None
        return target.read_bytes()
    except FileNotFoundError:
        # 删除或改名之后，工作区可能已经没有这一份，仍会查暂存/提交版本。
        return None


def versions(root, all_files):
    if all_files:
        for path in sorted(git_paths(root, "ls-files", "--cached", "-z")):
            yield path, "工作区", read_worktree(root, path)
        return

    staged = git_paths(root, "diff", "--cached", "--name-only", "-z",
                       "--diff-filter=ACMRT", "--no-renames", "--")
    unstaged = git_paths(root, "diff", "--name-only", "-z",
                         "--diff-filter=ACMRT", "--no-renames", "--")
    untracked = git_paths(root, "ls-files", "--others", "--exclude-standard", "-z")
    # origin/main 不存在就报错，不把待推送检查悄悄降级为空。
    commits = git(root, "rev-list", "--reverse", "origin/main..HEAD").splitlines()
    committed = []
    current = staged | unstaged | untracked
    for raw_commit in commits:
        commit = raw_commit.decode("ascii")
        paths = git_paths(root, "diff-tree", "--root", "--no-commit-id", "-r", "-m",
                          "--name-only", "-z", "--diff-filter=ACMRT", "--no-renames",
                          commit, "--")
        committed.append((commit, paths))
        current.update(paths)

    for path in sorted(current):
        yield path, "工作区", read_worktree(root, path)
    for path in sorted(staged):
        yield path, "暂存区", git(root, "show", f":0:{path}")
    for commit, paths in committed:
        for path in sorted(paths):
            yield path, f"提交 {commit[:12]}", git(root, "show", f"{commit}:{path}")


def check(root, all_files, names):
    count = 0
    seen = set()
    for path, source, data in versions(root, all_files):
        if data is None or b"\0" in data:
            continue
        fingerprint = (path, hashlib.sha256(data).digest())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for start, end, category in find_hits(line, names):
                # 不输出原始整行，避免相邻的其他敏感值跟着泄露。
                snippet = json.dumps(mask(line[start:end]), ensure_ascii=False)
                print(f"{safe_path(path, names)}:{line_number}: "
                      f"{category} {snippet} [{source}]")
                count += 1
    if count:
        print(f"隐私检查未通过：发现 {count} 处问题（命中内容已遮住）。")
        return 1
    print("隐私检查通过")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", dest="all_files",
                        help="检查全部被 Git 跟踪的 UTF-8 文本文件")
    args = parser.parse_args()
    # Windows 的输出编码可能表示不了文件名；不要因此打印含本机路径的异常。
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    try:
        root = Path(git(Path(__file__).resolve().parent,
                        "rev-parse", "--show-toplevel").decode("utf-8").strip())
        return check(root, args.all_files, username_patterns())
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        # Git 和系统异常可能夹带完整本机路径、用户名或凭证，不照抄异常文本。
        print("隐私检查未完成：无法读取 Git 数据或文件；"
              "请检查访问权限和仓库状态（默认模式需要 origin/main）。", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
