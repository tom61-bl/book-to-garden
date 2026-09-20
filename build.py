#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键生产：笔记 -> 卡片 -> .apkg -> 网页复习卡 + 精美阅读页。
用法:  python build.py
前置:  cd quartz && npm install ; pip install -r requirements.txt
"""
import subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
TOOLS = ROOT / "tools"

def run(cmd, cwd=ROOT):
    print(f"\n$ {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

if __name__ == "__main__":
    py = sys.executable
    run([py, "notes_to_cards.py"], cwd=TOOLS)
    run([py, "build_review_html.py"], cwd=TOOLS)
    run([py, "build_notes_html.py"], cwd=TOOLS)
    run(["md2anki", "out/cards.md", "-o-anki", "out/notes.apkg"], cwd=TOOLS)
    print("\n✅ 完成: tools/out/{cards.md, cards.json, review.html, notes.html, notes.apkg}")
