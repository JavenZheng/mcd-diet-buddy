#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
敏感信息扫描（推送前必跑）—— 麦当劳减肥拍档

扫描范围：仓库内所有**会被 git 提交**的文本文件（已排除 .git / .workbuddy / _site）。
命中项会列出 文件:行号:类型，并**以退出码 1 结束**（方便接 CI 或人工复核）。
本脚本只读，唔改任何文件。

用法：
    python scripts/secret_scan.py            # 扫仓库根目录
    python scripts/secret_scan.py --strict   # 连示例/占位符都报（默认已排除明显占位）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", ".workbuddy", "_site", "__pycache__", ".venv", "venv", "node_modules"}
SKIP_FILES = {"secret_scan.py"}          # 本脚本自带特征串，跳过自己
SCAN_EXT = {".py", ".md", ".json", ".yml", ".yaml", ".html", ".txt", ".example", ".gitignore"}

# ---- 特征规则 ----
RULES = [
    ("GitHub Token (ghp_)",        re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("GitHub Token (gho_)",        re.compile(r"gho_[A-Za-z0-9]{20,}")),
    ("GitHub Token (ghu_/ghs_)",   re.compile(r"ghu_[A-Za-z0-9]{20,}|ghs_[A-Za-z0-9]{20,}")),
    ("GitHub Token (github_pat_)", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("Fine-grained PAT",           re.compile(r"githubpat_[A-Za-z0-9_]{20,}")),
    ("Bearer 令牌",                 re.compile(r"Bearer\s+[A-Za-z0-9._\-]{20,}")),
    ("私钥标记",                     re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS Key",                    re.compile(r"AKIA[0-9A-Z]{16}")),
    ("硬编码口令",                   re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']", re.I)),
    ("11 位手机号",                  re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")),
]

# 明显嘅占位符 / 示例 / 文档说明 —— 唔算命中
PLACEHOLDER = re.compile(
    r"ghp_[Xx]{10,}|ghp_xxxxxxxxxxxx|xxxx+|YOUR_|<your|your_|<占位|示例|example|placeholder|"
    r"gh api|Authorization:|环境变量占位符|不曾|未存储|唔需要|不需要|唔索取|BUNDLE_TOKENS|id-token",
    re.I,
)


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES:
                continue
            ext = os.path.splitext(fn)[1]
            if ext not in SCAN_EXT and fn != ".gitignore":
                continue
            yield os.path.join(dirpath, fn)


def main():
    strict = "--strict" in sys.argv
    hits, scanned = [], 0
    for path in iter_files():
        rel = os.path.relpath(path, ROOT)
        try:
            text = open(path, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for i, line in enumerate(text.splitlines(), 1):
            for label, pat in RULES:
                m = pat.search(line)
                if not m:
                    continue
                if not strict and PLACEHOLDER.search(line):
                    continue          # 文档里讲「唔需要 token」之类，唔算
                snippet = line.strip()
                if len(snippet) > 120:
                    snippet = snippet[:117] + "..."
                hits.append((rel, i, label, snippet))

    print(f"扫描文件数：{scanned}（已排除 .git / .workbuddy / _site）")
    if not hits:
        print("✅ 全绿：未发现 token / 手机号 / 私钥等敏感特征串")
        return 0

    print(f"❌ 命中 {len(hits)} 处，请人工确认（本脚本未修改任何文件）：")
    for rel, ln, label, snippet in hits:
        print(f"   {rel}:{ln}  [{label}]  {snippet}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
