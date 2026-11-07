#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 GitHub Release 的旧附件：保留最近 N 个版本的附件，更早的只删附件、保留版本记录与更新说明。

为什么要保留记录：应用里的「更新日志」读的是 /releases?per_page=30，
删掉 Release 记录会让历史日志一起消失，所以只删附件。

用法：
    python scripts/clean-releases.py              # 保留最近 2 个版本
    python scripts/clean-releases.py --keep 3     # 保留最近 3 个
    python scripts/clean-releases.py --dry-run    # 只看会删什么
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

REPO = "steveliuyan/3d-print-cost-cn"
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET = os.path.join(REPO_DIR, ".secrets", "github-token.txt")


def load_token() -> str:
    if not os.path.exists(SECRET):
        raise SystemExit(f"没找到 token 文件: {SECRET}")
    for ln in open(SECRET, encoding="utf-8"):
        ln = ln.strip()
        if ln.startswith("GITHUB_TOKEN="):
            tok = ln.split("=", 1)[1].strip()
            if tok:
                return tok
    raise SystemExit("token 文件里没有 GITHUB_TOKEN=...")


def api(token: str, method: str, path: str):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Authorization": "Bearer " + token,
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def clean(keep: int = 2, dry_run: bool = False, token: str | None = None) -> dict:
    """保留最近 keep 个版本的附件，其余版本只删附件。返回统计。"""
    token = token or load_token()
    st, rels = api(token, "GET", f"/repos/{REPO}/releases?per_page=100")
    if st != 200 or not isinstance(rels, list):
        raise SystemExit(f"读取 Release 失败: {st} {rels}")

    # GitHub 返回按创建时间倒序，前 keep 个即最新
    keep_tags = [r["tag_name"] for r in rels[:keep]]
    freed = 0
    removed = 0
    touched = []
    for rel in rels[keep:]:
        if not rel["assets"]:
            continue
        for a in rel["assets"]:
            if dry_run:
                print(f"  [dry-run] 将删除 {rel['tag_name']} / {a['name']} "
                      f"({a['size'] / 1024 / 1024:.1f} MB)")
                freed += a["size"]
                removed += 1
                continue
            st2, _ = api(token, "DELETE", f"/repos/{REPO}/releases/assets/{a['id']}")
            if st2 in (200, 204):
                freed += a["size"]
                removed += 1
            else:
                print(f"  ⚠ 删除失败 {rel['tag_name']}/{a['name']}: HTTP {st2}")
        touched.append(rel["tag_name"])

    return {"keep": keep_tags, "removed": removed,
            "freed_mb": freed / 1024 / 1024, "touched": touched,
            "total_releases": len(rels), "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", type=int, default=2, help="保留最近几个版本的附件（默认 2）")
    ap.add_argument("--dry-run", action="store_true", help="只列出会删什么，不真删")
    args = ap.parse_args()

    res = clean(keep=max(1, args.keep), dry_run=args.dry_run)
    tag = "（dry-run）" if res["dry_run"] else ""
    print(f"\n[clean] 保留最近 {res['keep']} 个版本的附件{tag}: {', '.join(res['keep'])}")
    print(f"[clean] 共删附件 {res['removed']} 个，释放 {res['freed_mb']:.0f} MB；"
          f"Release 记录 {res['total_releases']} 条全部保留（更新日志不受影响）")


if __name__ == "__main__":
    main()
