#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一条命令发版：建 tag → 建 Release → 上传 dist/release 下的三个产物 → 自动清理旧附件。

用法：
    python scripts/release.py                    # 版本号取自 index.html 的 APP_VERSION
    python scripts/release.py --notes notes.md   # 从文件读更新说明（默认自动生成一份）
    python scripts/release.py --dry-run          # 只打印将要做什么

自动清理规则：**保留最近 2 个版本的附件，更早的只删附件、保留版本记录**
（应用内「更新日志」读的是 /releases，删记录会把历史日志一起删掉）。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "steveliuyan/3d-print-cost-cn"
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET = os.path.join(REPO_DIR, ".secrets", "github-token.txt")
DIST = os.path.join(REPO_DIR, "dist", "release")

sys.path.insert(0, os.path.join(REPO_DIR, "scripts"))
import clean_releases  # noqa: E402  （scripts/clean_releases.py）


def load_token() -> str:
    for ln in open(SECRET, encoding="utf-8"):
        ln = ln.strip()
        if ln.startswith("GITHUB_TOKEN="):
            t = ln.split("=", 1)[1].strip()
            if t:
                return t
    raise SystemExit("没找到 GITHUB_TOKEN")


def app_version() -> str:
    html = open(os.path.join(REPO_DIR, "index.html"), encoding="utf-8").read()
    m = re.search(r'var APP_VERSION = "([\d.]+)"', html)
    if not m:
        raise SystemExit("index.html 里找不到 APP_VERSION")
    return m.group(1)


def git_sha() -> str:
    for exe in ("git", r"C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe"):
        try:
            out = subprocess.run([exe, "rev-parse", "HEAD"], cwd=REPO_DIR,
                                 capture_output=True, text=True, timeout=30)
            if out.returncode == 0:
                return out.stdout.strip()
        except Exception:
            continue
    raise SystemExit("拿不到 git HEAD")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--notes", help="更新说明 markdown 文件")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ver = app_version()
    tag = "v" + ver
    sha = git_sha()
    token = load_token()

    assets = []
    for suffix, kind in (("web.html", "网页版"), ("portable.exe", "Windows"), ("apk", "Android")):
        p = os.path.join(DIST, f"3d-print-cost-cn-{ver}-{suffix}")
        if os.path.exists(p):
            assets.append((f"3d-print-cost-cn-{ver}-{suffix}", p, kind))
    if not assets:
        raise SystemExit(f"dist/release 下没有 {ver} 的产物，先打包")

    body = "## 本次更新\n\n（未提供更新说明）\n"
    if args.notes and os.path.exists(args.notes):
        body = open(args.notes, encoding="utf-8").read()

    print(f"[plan] tag={tag}  sha={sha[:9]}")
    print(f"[plan] 产物 {len(assets)} 个：")
    for name, p, _ in assets:
        print(f"         {name}  {os.path.getsize(p) / 1024 / 1024:.2f} MB")
    if args.dry_run:
        print("[plan] dry-run，结束")
        return

    H = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
         "User-Agent": "release-script"}

    def call(method, url, data=None):
        raw = json.dumps(data).encode() if data is not None else None
        h = dict(H)
        if raw:
            h["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=raw, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            return e.code, {"err": e.read().decode("utf-8", "replace")[:400]}

    def upload(url, path, name):
        with open(path, "rb") as f:
            data = f.read()
        h = dict(H)
        h["Content-Type"] = "application/octet-stream"
        req = urllib.request.Request(url + "?name=" + urllib.parse.quote(name),
                                     data=data, headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                return r.status, json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            return e.code, {"err": e.read().decode("utf-8", "replace")[:400]}

    st, resp = call("POST", f"https://api.github.com/repos/{REPO}/git/refs",
                    {"ref": "refs/tags/" + tag, "sha": sha})
    print(f"[tag] {st} {resp.get('ref', resp.get('err'))}")

    st, rel = call("POST", f"https://api.github.com/repos/{REPO}/releases",
                   {"tag_name": tag, "target_commitish": "main", "name": tag,
                    "body": body, "draft": False, "prerelease": False,
                    "make_latest": "true"})
    if st not in (200, 201):
        raise SystemExit(f"[release] 失败 {st} {rel}")
    print(f"[release] {st} {rel.get('html_url')}")

    upl = rel["upload_url"].split("{")[0]
    for name, path, _ in assets:
        st, a = upload(upl, path, name)
        print(f"[asset] {st} {name} local={os.path.getsize(path)} remote={a.get('size')}")

    st, latest = call("GET", f"https://api.github.com/repos/{REPO}/releases/latest")
    print(f"[check] latest={latest.get('tag_name')} assets={len(latest.get('assets') or [])}")

    # 自动清理：保留最近 2 个版本的附件
    print("\n[clean] 自动清理旧附件（保留最近 2 个版本）…")
    res = clean_releases.clean(keep=2, token=token)
    print(f"[clean] 保留 {', '.join(res['keep'])}；删了 {res['removed']} 个附件，"
          f"释放 {res['freed_mb']:.0f} MB；{res['total_releases']} 条版本记录全部保留")


if __name__ == "__main__":
    main()
