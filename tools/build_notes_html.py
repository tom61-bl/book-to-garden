#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 quartz/content/ 里的读书笔记渲染成 self-contained 精美 HTML 阅读器。
设计语言：Zara 式极简杂志风——暖白底、衬线大标题、大量留白、细线分隔。
输出 tools/out/notes.html"""
import re, json, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "quartz" / "content"
OUT = ROOT / "tools" / "out"


def parse_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).splitlines():
            mm = re.match(r"^(\w+):\s*(.*)$", line)
            if mm:
                k, v = mm.group(1), mm.group(2).strip()
                meta[k] = v.strip("[]").strip("'\"") if v.startswith("[") else v.strip("'\"")
        body = text[m.end():]
    return meta, body


def inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    return s


def render_md(md):
    out, in_ul, in_concept = [], False, False
    lines = md.split("\n")
    i = 0
    def close_ul():
        nonlocal in_ul
        if in_ul: out.append("</ul>"); in_ul = False
    def close_concept():
        nonlocal in_concept
        if in_concept: out.append("</div>"); in_concept = False
    while i < len(lines):
        line = lines[i].rstrip()
        m = re.match(r"^>\s*\[!(summary|quote|tip|note)\]\s*(.*)$", line)
        if m:
            close_ul(); close_concept()
            kind = m.group(1)
            buf = [m.group(2)]
            while i + 1 < len(lines) and re.match(r"^>\s?", lines[i + 1]):
                i += 1
                buf.append(re.sub(r"^>\s?", "", lines[i]).strip())
            text = inline(" ".join(x for x in buf if x))
            label = {"summary": "精华", "quote": "金句", "tip": "提示", "note": "笔记"}[kind]
            cls = "callout " + ("callout-quote" if kind == "quote" else "callout-summary")
            qmark = '<div class="qmark">&#8220;</div>' if kind == "quote" else ""
            out.append(f'<div class="{cls}"><span class="callout-label">{label}</span>{qmark}<p>{text}</p></div>')
            i += 1; continue
        if line.startswith("### "):
            close_ul(); close_concept()
            out.append(f'<div class="concept"><span class="concept-tag">CONCEPT</span><h3>{inline(line[4:])}</h3>')
            in_concept = True
            i += 1; continue
        if line.startswith("## "):
            close_ul(); close_concept()
            out.append(f'<h2>{inline(line[3:])}</h2>'); i += 1; continue
        if line.startswith("# "):
            close_ul(); close_concept()
            out.append(f'<h1>{inline(line[2:])}</h1>'); i += 1; continue
        if re.match(r"^[-*] ", line):
            if not in_ul: out.append("<ul>"); in_ul = True
            out.append(f"<li>{inline(re.sub(r'^[-*] ','',line))}</li>")
            i += 1; continue
        if line == "":
            close_ul(); i += 1; continue
        close_ul()
        out.append(f"<p>{inline(line)}</p>")
        i += 1
    close_ul(); close_concept()
    return "\n".join(out)


books = []
for f in sorted(CONTENT.glob("*.md")):
    if f.name == "index.md":
        continue
    text = f.read_text(encoding="utf-8")
    meta, body = parse_fm(text)
    books.append({
        "id": f.stem,
        "title": meta.get("title", f.stem),
        "author": meta.get("author", ""),
        "tags": meta.get("tags", ""),
        "html": render_md(body),
    })

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reading Journal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Work+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --paper:#F2EEDF; --paper-2:#ECE6D2; --ink:#2A241B; --ink-soft:#5C5345;
    --pink:#E1A4C2; --lemon:#D6DD63; --blush:#E8C9B6; --sage:#B7C7A8;
    --serif:"Cormorant Garamond","Noto Serif SC",Georgia,serif;
    --sans:"Work Sans","PingFang SC","Microsoft YaHei",sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--sans);background:var(--paper);color:var(--ink);font-weight:300;-webkit-font-smoothing:antialiased}
  .app{display:flex;min-height:100vh}
  .sidebar{width:260px;flex-shrink:0;border-right:1px solid rgba(42,36,27,.15);padding:48px 32px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column;background:var(--paper)}
  .brand{font-family:var(--serif);font-size:28px;font-weight:500;line-height:1}
  .brand small{display:block;font-family:var(--sans);font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft);margin-top:10px}
  .swatches{display:flex;gap:8px;margin-top:20px}
  .swatches i{width:18px;height:18px;border-radius:50%;display:block}
  .rule{height:1px;background:rgba(42,36,27,.2);margin:28px 0}
  .nav{display:flex;flex-direction:column;gap:2px;overflow:auto;flex:1}
  .nav a{padding:9px 0;color:var(--ink-soft);text-decoration:none;font-size:13px;letter-spacing:.3px;cursor:pointer;border-bottom:1px solid transparent;transition:.2s;font-family:var(--serif);font-size:16px}
  .nav a:hover{color:var(--ink)}
  .nav a.active{color:var(--ink);border-bottom-color:var(--pink)}
  .review-btn{margin-top:24px;padding:13px 0;text-align:center;background:var(--lemon);color:var(--ink);text-decoration:none;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:500;transition:.25s}
  .review-btn:hover{background:var(--ink);color:var(--paper)}
  .content{flex:1;padding:72px 10vw;max-width:860px}
  .book-head{margin-bottom:56px}
  .book-head .author{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);margin-bottom:18px}
  .book-head h1{font-family:var(--serif);font-size:52px;line-height:1.05;font-weight:500;letter-spacing:-.01em}
  .book-head .meta-line{height:3px;width:80px;background:var(--pink);margin-top:28px}
  .content h2{font-family:var(--serif);font-size:30px;font-weight:600;margin:56px 0 22px}
  .content p{font-size:16px;line-height:1.95;color:var(--ink);margin:18px 0}
  .content p:first-of-type::first-letter{font-family:var(--serif);font-size:68px;float:left;line-height:.85;padding:6px 12px 0 0;font-weight:500}
  .content ul{margin:18px 0;list-style:none}
  .content li{font-size:15px;line-height:1.9;color:var(--ink);padding:10px 0 10px 24px;position:relative;border-bottom:1px dashed rgba(42,36,27,.2)}
  .content li:before{content:"—";position:absolute;left:0;color:var(--pink)}
  .concept{background:rgba(255,255,255,.55);border-radius:18px;padding:28px 32px;margin:24px 0}
  .concept-tag{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft)}
  .concept h3{font-family:var(--serif);font-size:22px;font-weight:600;margin:10px 0 12px}
  .concept p{margin:6px 0;font-size:15.5px;line-height:1.85}
  .callout{margin:48px 0;padding:40px;text-align:center;position:relative}
  .callout-label{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft)}
  .callout-summary p{font-family:var(--serif);font-size:22px;line-height:1.6;margin:18px 0 0;font-style:italic;color:var(--ink)}
  .callout-quote{border-top:1px solid rgba(42,36,27,.2);border-bottom:1px solid rgba(42,36,27,.2)}
  .callout-quote .qmark{font-family:var(--serif);font-size:80px;line-height:.4;color:var(--blush);margin-bottom:18px}
  .callout-quote p{font-family:var(--serif);font-size:32px;line-height:1.35;font-weight:500;font-style:italic;margin:0;color:var(--ink)}
  strong{font-weight:600;color:var(--ink)}
  @media(max-width:760px){.sidebar{display:none}.content{padding:48px 24px}.book-head h1{font-size:36px}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">Reading Journal<small>笔记 · 读书笔记</small></div>
    <div class="rule"></div>
    <nav class="nav" id="nav"></nav>
    <a class="review-btn" href="review.html">Review Cards</a>
  </aside>
  <main class="content" id="main"></main>
</div>
<script>
const BOOKS = __BOOKS__;
const nav = document.getElementById("nav"), main = document.getElementById("main");
function show(id){
  const b = BOOKS.find(x=>x.id===id) || BOOKS[0];
  document.querySelectorAll(".nav a").forEach(a=>a.classList.toggle("active", a.dataset.id===b.id));
  main.innerHTML = `<div class="book-head"><div class="author">${b.author}</div><h1>${b.title}</h1><div class="meta-line"></div></div>` + b.html;
  window.scrollTo(0,0);
}
BOOKS.forEach(b=>{
  const a=document.createElement("a"); a.dataset.id=b.id; a.textContent=b.title; a.onclick=()=>show(b.id);
  nav.appendChild(a);
});
show(BOOKS[0].id);
</script>
</body>
</html>
"""

payload = json.dumps(books, ensure_ascii=False).replace("</", "<\\/")
out = TEMPLATE.replace("__BOOKS__", payload)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "notes.html").write_text(out, encoding="utf-8")
print(f"[build_notes_html] {len(books)} books -> out/notes.html ({len(out)} bytes)")
