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
            out.append(f'<div class="{cls}"><span class="callout-label">{label}</span><p>{text}</p></div>')
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
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root{
    --bg:#f7f4ee; --ink:#1a1a1a; --sub:#8c867c; --line:#ddd7cb;
    --serif:"Playfair Display","Noto Serif SC",Georgia,serif;
    --sans:"Inter","PingFang SC","Microsoft YaHei",sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--sans);background:var(--bg);color:var(--ink);font-weight:300;-webkit-font-smoothing:antialiased}
  .app{display:flex;min-height:100vh}
  /* sidebar */
  .sidebar{width:240px;flex-shrink:0;border-right:1px solid var(--line);padding:48px 32px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column}
  .brand{font-family:var(--serif);font-size:22px;letter-spacing:.5px}
  .brand small{display:block;font-family:var(--sans);font-size:10px;letter:3px;text-transform:uppercase;color:var(--sub);margin-top:8px}
  .rule{height:1px;background:var(--line);margin:28px 0}
  .nav{display:flex;flex-direction:column;gap:2px;overflow:auto;flex:1}
  .nav a{padding:8px 0;color:var(--sub);text-decoration:none;font-size:13px;letter-spacing:.5px;cursor:pointer;border-bottom:1px solid transparent;transition:.2s}
  .nav a:hover{color:var(--ink)}
  .nav a.active{color:var(--ink);border-bottom-color:var(--ink)}
  .review-btn{margin-top:24px;padding:13px 0;text-align:center;border:1px solid var(--ink);color:var(--ink);text-decoration:none;font-size:11px;letter-spacing:2px;text-transform:uppercase;transition:.25s}
  .review-btn:hover{background:var(--ink);color:var(--bg)}
  /* content */
  .content{flex:1;padding:72px 12vw;max-width:880px}
  .book-head{margin-bottom:64px}
  .book-head .author{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--sub);margin-bottom:18px}
  .book-head h1{font-family:var(--serif);font-size:42px;line-height:1.25;font-weight:600}
  .book-head .meta-line{height:1px;background:var(--ink);width:60px;margin-top:32px}
  .content h2{font-family:var(--serif);font-size:24px;font-weight:600;margin:56px 0 22px}
  .content p{font-size:16px;line-height:2;color:#2c2c2c;margin:18px 0}
  .content ul{margin:18px 0;list-style:none}
  .content li{font-size:15.5px;line-height:2;color:#2c2c2c;padding:8px 0 8px 24px;position:relative;border-bottom:1px solid #efece4}
  .content li:before{content:"—";position:absolute;left:0;color:var(--sub)}
  .concept{margin:32px 0;padding:28px 0;border-top:1px solid var(--line)}
  .concept-tag{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--sub)}
  .concept h3{font-family:var(--serif);font-size:20px;font-weight:600;margin:10px 0 14px}
  .concept p{margin:8px 0;font-size:15.5px;line-height:1.95}
  .callout{margin:44px 0;padding:36px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
  .callout-label{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--sub)}
  .callout-summary p{font-family:var(--serif);font-size:19px;line-height:1.7;margin:14px 0 0;font-style:italic}
  .callout-quote{text-align:center}
  .callout-quote p{font-family:var(--serif);font-size:26px;line-height:1.6;font-style:italic;margin:20px 0 0;color:var(--ink)}
  strong{font-weight:500}
  @media(max-width:760px){.sidebar{display:none}.content{padding:48px 28px}.book-head h1{font-size:32px}}
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

payload = html.escape(json.dumps(books, ensure_ascii=False))
out = TEMPLATE.replace("__BOOKS__", payload)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "notes.html").write_text(out, encoding="utf-8")
print(f"[build_notes_html] {len(books)} books -> out/notes.html ({len(out)} bytes)")
