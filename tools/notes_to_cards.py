#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提炼层：读 Quartz content/ 里的读书笔记，
  -> tools/out/cards.md     （喂给 md2anki 导出 .apkg）
  -> tools/out/cards.json   （喂给网页复习卡）

读书笔记约定（在 content/*.md 里写）：
  frontmatter: title / author / tags
  ### 概念名        -> 自动生成 Q&A 卡（"什么是概念名？" + 下面段落作答案）
  - 问：… 答：…     -> 直接生成 Q&A 卡
  > [!quote]        -> 金句卡
"""
import re, json, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "quartz" / "content"
OUT = ROOT / "tools" / "out"
DECK_UUID = "583813da-5766-4cb8-b39f-ae0337e0000"


def stable_uuid(*parts: str) -> str:
    h = hashlib.md5("||".join(parts).encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def parse_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^(\w+):\s*(.*)$", line)
            if mm:
                k, v = mm.group(1), mm.group(2).strip()
                if v.startswith("["):
                    v = [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]
                else:
                    v = v.strip("'\"")
                meta[k] = v
        body = text[m.end():]
    return meta, body


def extract_cards(book: str, body: str):
    cards = []

    # 1) ### 概念名 -> Q&A
    for sec in re.split(r"\n### ", body)[1:]:
        head, _, rest = sec.partition("\n")
        title = head.strip()
        rest = re.split(r"\n## ", rest)[0]
        ans = re.sub(r"\*\s*（可挖空：[^）]*）\*", "", rest).strip()
        if title and ans:
            cards.append({"type": "qa", "front": f"什么是「{title}」？", "back": ans, "source": book})

    # 2) - 问：… 答：…
    for m in re.finditer(r"[-*]\s*问：(.+?)\s*答：(.+?)(?=\n[-*]|\n##|\Z)", body, re.S):
        cards.append({"type": "qa", "front": m.group(1).strip(), "back": m.group(2).strip(), "source": book})

    # 3) > [!quote] 金句
    for m in re.finditer(r">\s*\[!quote\][^\n]*\n\s*>\s*(.+)", body):
        cards.append({"type": "quote", "front": f"金句出自《{book}》，原文是哪一句？", "back": m.group(1).strip(), "source": book})

    return cards


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    all_cards, md_lines = [], [f"# 读书笔记合集 ({DECK_UUID})", ""]
    for md in sorted(CONTENT.glob("*.md")):
        meta, body = parse_frontmatter(md.read_text(encoding="utf-8"))
        book = meta.get("title", md.stem)
        for c in extract_cards(book, body):
            c["id"] = stable_uuid(book, c["front"])
            all_cards.append(c)
            md_lines.append(f"## {c['front']} ({c['id']})")
            md_lines.append(c["back"])
            md_lines.append("")

    (OUT / "cards.md").write_text("\n".join(md_lines), encoding="utf-8")
    (OUT / "cards.json").write_text(json.dumps({"deck": "读书笔记", "cards": all_cards},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[notes_to_cards] {len(all_cards)} cards -> out/cards.md + cards.json")


if __name__ == "__main__":
    main()
