#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 quartz/content/ 里的读书笔记渲染成 self-contained 精美 HTML 阅读器。
杂志风（Soft Editorial）+ 互动：概念折叠（提取练习）+ 每篇末尾小测（测试效应）。
输出 tools/out/notes.html"""
import re, json, pathlib, html, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT = ROOT / "quartz" / "content"
OUT = ROOT / "tools" / "out"
random.seed(42)


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


def render_md(md, section_quiz):
    """section_quiz: callable(section_title, concepts) -> quiz HTML 片段，由外层注入。"""
    out, in_ul = [], False
    cur_concept_open = False       # concept 与 concept-body 两层 div 是否都开着
    cur_section = None
    cur_section_concepts = []       # [(title, )] 用于小节小测

    def close_ul():
        nonlocal in_ul
        if in_ul: out.append("</ul>"); in_ul = False
    def close_concept():
        nonlocal cur_concept_open
        if cur_concept_open:
            out.append("</div></div>")   # 先关 concept-body，再关 concept
            cur_concept_open = False
    def flush_section_quiz():
        nonlocal cur_section_concepts
        if cur_section and len(cur_section_concepts) >= 2:
            out.append(section_quiz(cur_section, cur_section_concepts))
        cur_section_concepts = []

    lines = md.split("\n")
    i = 0
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
            title = inline(line[4:])
            raw_title = re.sub(r"[*_`]", "", line[4:]).strip()
            cur_section_concepts.append(raw_title)
            out.append(
                f'<div class="concept" onclick="this.classList.toggle(\'open\')">'
                f'<div class="concept-head"><span class="concept-tag">CONCEPT</span>'
                f'<h3>{title}</h3>'
                f'<span class="concept-reveal">回忆 / 显示答案</span></div>'
                f'<div class="concept-body">'
            )
            cur_concept_open = True
            i += 1; continue
        if line.startswith("## "):
            close_ul(); close_concept()
            flush_section_quiz()
            cur_section = re.sub(r"[*_`]", "", line[3:]).strip()
            out.append(f'<h2>{inline(line[3:])}</h2>'); i += 1; continue
        if line.startswith("# "):
            close_ul(); close_concept()
            flush_section_quiz()
            cur_section = None
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
    flush_section_quiz()
    return "\n".join(out)


def build_quiz(cards):
    by_book = {"__all__": cards}
    for c in cards:
        by_book.setdefault(c["source"], []).append(c)
    all_qs = [c["front"] for c in cards]
    quizzes = {}
    for book, cs in by_book.items():
        if book == "__all__":
            continue
        qa = [c for c in cs if c["type"] == "qa"]
        random.shuffle(qa)
        items = []
        for c in qa[:3]:
            ans = c["back"].split("。")[0][:40]
            wrong = random.sample([q for q in all_qs if q != c["front"]], min(3, len(all_qs)-1))
            opts = [ans] + wrong
            random.shuffle(opts)
            items.append({"q": c["front"], "a": ans, "opts": opts})
        quizzes[book] = items
    return quizzes


def build_section_quiz_factory(book_quiz, all_fronts, rng):
    """返回一个 section_quiz(section_title, concepts) -> html 函数。
    每调用一次（即每个 ## 小节末尾）就从 book_quiz 里取一道题。"""
    pool = list(book_quiz)
    rng.shuffle(pool)
    idx = [0]
    def make(section_title, concepts):
        if idx[0] >= len(pool):
            return ""
        item = pool[idx[0]]; idx[0] += 1
        wrong = rng.sample([f for f in all_fronts if f != item["q"]], min(3, len(all_fronts)-1))
        opts = [item["a"]] + wrong
        rng.shuffle(opts)
        opts_json = json.dumps(opts, ensure_ascii=False)
        return (
            f'<div class="mini-quiz">'
            f'<div class="mini-quiz-label">本节小测 · {html.escape(section_title)}</div>'
            f'<div class="mini-quiz-q">{html.escape(item["q"])}</div>'
            f'<div class="mini-quiz-opts" data-answer="{html.escape(item["a"])}" data-opts=\'{opts_json}\'>'
            + "".join(f'<button class="mini-opt">{html.escape(o)}</button>' for o in opts)
            + '</div><div class="mini-quiz-fb" style="display:none"></div>'
            f'</div>'
        )
    return make


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
    })

cards = json.loads((OUT / "cards.json").read_text(encoding="utf-8")) if (OUT / "cards.json").exists() else {"cards": []}
all_cards = cards["cards"]
all_fronts = list({c["front"] for c in all_cards})

# 按书分组，每本书的 quiz pool：从该书的 qa 卡片里抽
by_book = {}
for c in all_cards:
    if c["type"] == "qa":
        by_book.setdefault(c["source"], []).append(c)

# 每本书出够多的题（按书内卡片数，上限 8 道，足够覆盖所有 ## 小节）
rng = random.Random(42)
for b in books:
    pool_cards = by_book.get(b["title"], [])
    quiz_items = []
    for c in pool_cards:
        ans = c["back"].split("。")[0][:60]
        quiz_items.append({"q": c["front"], "a": ans})
    rng.shuffle(quiz_items)
    b["quiz_pool"] = quiz_items[:8]
    # 整本书末尾的总小测（需要 opts 字段供 quizHtml 渲染选项）
    final_quiz = []
    for item in quiz_items[:3]:
        wrong = rng.sample([f for f in all_fronts if f != item["q"]], min(3, len(all_fronts)-1))
        opts = [item["a"]] + wrong
        rng.shuffle(opts)
        final_quiz.append({"q": item["q"], "a": item["a"], "opts": opts})
    b["quiz"] = final_quiz

# 第二遍渲染：每本书注入自己的 section_quiz 工厂
for b in books:
    factory = build_section_quiz_factory(b["quiz_pool"], all_fronts, random.Random(hash(b["id"]) & 0xFFFF))
    md_text = (CONTENT / (b["id"] + ".md")).read_text(encoding="utf-8")
    _, body = parse_fm(md_text)
    b["html"] = render_md(body, factory)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Reading Journal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Work+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root{--paper:#F2EEDF;--paper-2:#ECE6D2;--ink:#2A241B;--ink-soft:#5C5345;--pink:#E1A4C2;--lemon:#D6DD63;--blush:#E8C9B6;--sage:#B7C7A8;
    --serif:"Cormorant Garamond","Noto Serif SC",Georgia,serif;--sans:"Work Sans","PingFang SC","Microsoft YaHei",sans-serif;}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:var(--sans);background:var(--paper);color:var(--ink);font-weight:300;-webkit-font-smoothing:antialiased}
  .app{display:flex;min-height:100vh}
  .sidebar{width:260px;flex-shrink:0;border-right:1px solid rgba(42,36,27,.15);padding:48px 32px;position:sticky;top:0;height:100vh;display:flex;flex-direction:column}
  .brand{font-family:var(--serif);font-size:28px;font-weight:500;line-height:1}
  .brand small{display:block;font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft);margin-top:10px}
  .swatches{display:flex;gap:8px;margin-top:20px}
  .swatches i{width:18px;height:18px;border-radius:50%;display:block}
  .rule{height:1px;background:rgba(42,36,27,.2);margin:28px 0}
  .nav{display:flex;flex-direction:column;gap:2px;overflow:auto;flex:1}
  .nav a{padding:9px 0;color:var(--ink-soft);text-decoration:none;font-size:16px;cursor:pointer;border-bottom:1px solid transparent;transition:.2s;font-family:var(--serif)}
  .nav a:hover{color:var(--ink)}
  .nav a.active{color:var(--ink);border-bottom-color:var(--pink)}
  .review-btn{margin-top:24px;padding:13px 0;text-align:center;background:var(--lemon);color:var(--ink);text-decoration:none;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:500;transition:.25s}
  .review-btn:hover{background:var(--ink);color:var(--paper)}
  .content{flex:1;padding:72px 6vw;max-width:none}
  .book-head{margin-bottom:56px}
  .book-head .author{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);margin-bottom:18px}
  .book-head h1{font-family:var(--serif);font-size:52px;line-height:1.05;font-weight:500;letter-spacing:-.01em}
  .book-head .meta-line{height:3px;width:80px;background:var(--pink);margin-top:28px}
  .content h2{font-family:var(--serif);font-size:30px;font-weight:600;margin:56px 0 22px}
  .content p{font-size:16px;line-height:1.95;color:var(--ink);margin:18px 0}
  .content p:first-of-type::first-letter{font-family:var(--serif);font-size:68px;float:left;line-height:.85;padding:6px 12px 0 0;font-weight:500}
  .content ul{margin:18px 0;list-style:none}
  .content li{font-size:15px;line-height:1.9;color:var(--ink);padding:10px 0 10px 24px;position:relative;border-bottom:1px dashed rgba(42,36,27,.2)}
  .content li:before{content:"\2014";position:absolute;left:0;color:var(--pink)}
  .concept{background:rgba(255,255,255,.55);border-radius:18px;padding:0;margin:24px 0;cursor:pointer;transition:.2s;border:1px solid transparent}
  .concept:hover{border-color:rgba(42,36,27,.15)}
  .concept-head{padding:20px 28px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
  .concept-tag{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft)}
  .concept h3{font-family:var(--serif);font-size:20px;font-weight:600;flex:1}
  .concept-reveal{font-size:11px;letter-spacing:1px;color:var(--pink);text-transform:uppercase}
  .concept-body{display:none;padding:0 28px 22px}
  .concept.open .concept-body{display:block}
  .concept.open .concept-reveal{color:var(--sage)}
  .concept-body p{margin:6px 0;font-size:15.5px;line-height:1.85}
  .callout{margin:48px 0;padding:40px;text-align:center}
  .callout-label{font-size:10px;letter-spacing:3px;text-transform:uppercase;color:var(--ink-soft)}
  .callout-summary p{font-family:var(--serif);font-size:22px;line-height:1.6;margin:18px 0 0;font-style:italic}
  .callout-quote{border-top:1px solid rgba(42,36,27,.2);border-bottom:1px solid rgba(42,36,27,.2)}
  .callout-quote .qmark{font-family:var(--serif);font-size:80px;line-height:.4;color:var(--blush);margin-bottom:18px}
  .callout-quote p{font-family:var(--serif);font-size:32px;line-height:1.35;font-weight:500;font-style:italic;margin:0}
  strong{font-weight:600}
  .quiz{margin:64px 0 0;padding:36px;background:var(--paper-2);border-radius:20px}
  .quiz-title{font-family:var(--serif);font-size:24px;font-weight:600;margin-bottom:6px}
  .quiz-sub{font-size:12px;color:var(--ink-soft);letter-spacing:1px;margin-bottom:24px}
  .quiz-q{margin-bottom:22px}
  .quiz-q .qq{font-family:var(--serif);font-size:18px;margin-bottom:12px}
  .quiz-opts{display:flex;flex-direction:column;gap:8px}
  .quiz-opt{padding:11px 16px;border:1px solid rgba(42,36,27,.2);border-radius:10px;cursor:pointer;font-size:14px;transition:.15s;background:transparent;text-align:left;color:var(--ink);font-family:var(--sans)}
  .quiz-opt:hover{border-color:var(--ink)}
  .quiz-opt.right{background:var(--sage);border-color:var(--sage)}
  .quiz-opt.wrong{background:var(--pink);border-color:var(--pink)}
  .quiz-opt:disabled{cursor:default;opacity:.85}
  .quiz-score{margin-top:18px;font-family:var(--serif);font-size:18px;color:var(--ink-soft)}
  .mini-quiz{margin:28px 0 8px;padding:20px 24px;background:rgba(255,255,255,.6);border-left:3px solid var(--lemon);border-radius:0 12px 12px 0}
  .mini-quiz-label{font-size:10px;letter-spacing:2px;text-transform:uppercase;color:var(--ink-soft);margin-bottom:8px}
  .mini-quiz-q{font-family:var(--serif);font-size:17px;margin-bottom:12px;line-height:1.5}
  .mini-quiz-opts{display:flex;flex-direction:column;gap:6px}
  .mini-opt{padding:9px 14px;border:1px solid rgba(42,36,27,.18);border-radius:8px;cursor:pointer;font-size:13.5px;text-align:left;background:transparent;color:var(--ink);font-family:var(--sans);transition:.15s}
  .mini-opt:hover{border-color:var(--ink)}
  .mini-opt.right{background:var(--sage);border-color:var(--sage);color:var(--ink)}
  .mini-opt.wrong{background:var(--pink);border-color:var(--pink)}
  .mini-opt:disabled{cursor:default;opacity:.9}
  .mini-quiz-fb{margin-top:10px;font-size:13px;color:var(--ink-soft);font-style:italic}
  @media(max-width:760px){.sidebar{display:none}.content{padding:48px 24px}.book-head h1{font-size:36px}}
</style>
</head>
<body>
<div class="app">
  <aside class="sidebar">
    <div class="brand">Reading Journal<small>笔记 · 读书笔记</small></div>
    <div class="swatches"><i style="background:var(--pink)"></i><i style="background:var(--lemon)"></i><i style="background:var(--blush)"></i></div>
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
  main.innerHTML = `<div class="book-head"><div class="author">${b.author}</div><h1>${b.title}</h1><div class="meta-line"></div></div>` + b.html + quizHtml(b);
  window.scrollTo(0,0);
  bindQuiz(b);
  bindMiniQuiz();
}
function bindMiniQuiz(){
  document.querySelectorAll(".mini-quiz").forEach(mq=>{
    const ans = mq.querySelector(".mini-quiz-opts").dataset.answer;
    const fb = mq.querySelector(".mini-quiz-fb");
    mq.querySelectorAll(".mini-opt").forEach(btn=>{
      btn.onclick=()=>{
        mq.querySelectorAll(".mini-opt").forEach(x=>{x.disabled=true; if(x.textContent===ans) x.classList.add("right");});
        if(btn.textContent!==ans) btn.classList.add("wrong");
        fb.style.display="block";
        fb.textContent = btn.textContent===ans ? "✓ 答对了" : "✗ 正确答案：" + ans;
      };
    });
  });
}
function quizHtml(b){
  if(!b.quiz || !b.quiz.length) return "";
  return `<div class="quiz"><div class="quiz-title">小测一下</div><div class="quiz-sub">先别翻回去，凭印象选 —— 这才是真正的记忆</div>` +
    b.quiz.map((q,i)=>`<div class="quiz-q" data-i="${i}"><div class="qq">${i+1}. ${q.q}</div><div class="quiz-opts">` +
      q.opts.map(o=>`<button class="quiz-opt" data-a="${o===q.a}">${o}</button>`).join("") +
      `</div></div>`).join("") +
    `<div class="quiz-score" id="qs-${b.id}"></div></div>`;
}
function bindQuiz(b){
  document.querySelectorAll(".quiz-q").forEach(q=>{
    const ans = b.quiz[+q.dataset.i].a;
    q.querySelectorAll(".quiz-opt").forEach(btn=>{
      btn.onclick=()=>{
        q.querySelectorAll(".quiz-opt").forEach(x=>{x.disabled=true; if(x.dataset.a==="true") x.classList.add("right");});
        if(btn.dataset.a!=="true") btn.classList.add("wrong");
        const done=document.querySelectorAll(".quiz-q .quiz-opt.right").length;
        const all=document.querySelectorAll(".quiz-q").length;
        const el=document.getElementById("qs-"+b.id);
        if(done===all) el.textContent = all===3 ? "全对，这本书你吃透了 \u2726" : `答对 ${done} / ${all}`;
      };
    });
  });
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
