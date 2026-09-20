#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读 out/cards.json -> 生成 self-contained 的 out/review.html
翻牌复习 + 简化 SM-2 间隔重复，进度存 localStorage，双击即可打开。"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tools" / "out"

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>读书笔记 · 复习卡</title>
<style>
  :root { --bg:#0f1117; --card:#1a1d27; --ink:#e8e8ea; --sub:#9aa0ae; --accent:#6ea8fe; --good:#34c98e; --hard:#e0a94a; --again:#e5616b; --easy:#7b97aa; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
         background:radial-gradient(1200px 600px at 50% -10%, #1c2233, var(--bg)); color:var(--ink);
         min-height:100vh; display:flex; flex-direction:column; align-items:center; padding:24px 16px; }
  .top { width:100%; max-width:680px; display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; }
  .top h1 { font-size:16px; font-weight:600; }
  .top .meta { font-size:13px; color:var(--sub); }
  .deck { width:100%; max-width:680px; height:340px; perspective:1400px; cursor:pointer; }
  .flipper { position:relative; width:100%; height:100%; transition:transform .5s cubic-bezier(.2,.7,.3,1); transform-style:preserve-3d; }
  .deck.flipped .flipper { transform:rotateY(180deg); }
  .face { position:absolute; inset:0; backface-visibility:hidden; border-radius:20px; padding:36px;
          background:var(--card); border:1px solid #2a2e3d; box-shadow:0 20px 60px rgba(0,0,0,.45);
          display:flex; flex-direction:column; justify-content:center; }
  .face.back { transform:rotateY(180deg); }
  .tag { font-size:12px; color:var(--accent); letter-spacing:.5px; margin-bottom:14px; text-transform:uppercase; }
  .q { font-size:24px; line-height:1.5; font-weight:600; }
  .a { font-size:19px; line-height:1.7; color:var(--ink); }
  .src { margin-top:18px; font-size:13px; color:var(--sub); }
  .hint { margin-top:26px; font-size:12px; color:#5a6070; text-align:center; }
  .actions { width:100%; max-width:680px; display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:22px; }
  button { border:none; border-radius:12px; padding:14px 8px; font-size:14px; font-weight:600; color:#fff; cursor:pointer;
           transition:transform .1s, filter .15s; }
  button:hover { filter:brightness(1.15); transform:translateY(-1px); }
  .again { background:var(--again); } .hard { background:var(--hard); }
  .good { background:var(--good); } .easy { background:var(--easy); }
  .actions button:disabled { opacity:.35; cursor:not-allowed; }
  .done { text-align:center; padding:60px 0; }
  .done .big { font-size:48px; margin-bottom:10px; }
  kbd { background:#2a2e3d; border-radius:4px; padding:1px 6px; font-size:11px; }
</style>
</head>
<body>
  <div class="top">
    <h1>读书笔记 · 复习</h1>
    <div class="meta" id="meta"></div>
  </div>
  <div class="deck" id="deck">
    <div class="flipper">
      <div class="face front">
        <div class="tag" id="tag">问题</div>
        <div class="q" id="question"></div>
        <div class="hint">点击卡片或按 <kbd>空格</kbd> 翻面</div>
      </div>
      <div class="face back">
        <div class="tag">答案</div>
        <div class="a" id="answer"></div>
        <div class="src" id="source"></div>
      </div>
    </div>
  </div>
  <div class="actions" id="actions" style="visibility:hidden">
    <button class="again" data-g="0">再来一次<br><small>1</small></button>
    <button class="hard" data-g="3">困难<br><small>2</small></button>
    <button class="good" data-g="4">良好<br><small>3</small></button>
    <button class="easy" data-g="5">简单<br><small>4</small></button>
  </div>
<script>
const CARDS = __CARDS_JSON__;
const KEY = "review_srs_state_v1";
let state = JSON.parse(localStorage.getItem(KEY) || "{}");
let queue = [], idx = 0;

function today(){ return Math.floor(Date.now()/86400000); }
function getSRS(c){ return state[c.id] || {due: today(), ivl:0, reps:0, ease:2.5}; }

function buildQueue(){
  const t = today();
  queue = CARDS.cards.filter(c => getSRS(c).due <= t)
                     .sort((a,b)=> getSRS(a).due - getSRS(b).due);
  idx = 0;
  render();
}
function render(){
  const meta = document.getElementById("meta");
  const deck = document.getElementById("deck");
  const actions = document.getElementById("actions");
  if (idx >= queue.length){
    deck.innerHTML = '<div class="done"><div class="big">🌱</div><div style="font-size:20px;font-weight:600">今日复习完成</div><div class="hint" style="margin-top:10px">明天再来，或按 <kbd>R</kbd> 重学全部</div></div>';
    actions.style.visibility = "hidden";
    meta.textContent = "完成";
    return;
  }
  const c = queue[idx];
  deck.classList.remove("flipped");
  document.getElementById("tag").textContent = c.type === "quote" ? "金句" : "概念";
  document.getElementById("question").textContent = c.front;
  document.getElementById("answer").textContent = c.back;
  document.getElementById("source").textContent = "来源：《" + c.source + "》";
  meta.textContent = (idx+1) + " / " + queue.length + " · 今日剩余";
  setTimeout(()=>{ actions.style.visibility="visible"; }, 500);
}
function grade(g){
  const c = queue[idx], s = getSRS(c);
  if (g === 0){ s.ivl = 0; s.reps = 0; s.ease = Math.max(1.3, s.ease - 0.2); }
  else {
    s.reps += 1;
    if (g === 3){ s.ease -= 0.15; s.ivl = Math.max(1, Math.round(s.ivl * 1.2)); }
    else if (g === 4){ s.ivl = s.ivl <= 0 ? 1 : (s.ivl === 1 ? 3 : Math.round(s.ivl * s.ease)); }
    else if (g === 5){ s.ivl = s.ivl <= 0 ? 3 : Math.round(s.ivl * s.ease * 1.3); s.ease += 0.15; }
  }
  s.due = today() + s.ivl;
  state[c.id] = s;
  localStorage.setItem(KEY, JSON.stringify(state));
  idx++; render();
}
document.getElementById("deck").addEventListener("click", ()=>{
  if (idx < queue.length) document.getElementById("deck").classList.toggle("flipped");
});
document.querySelectorAll("#actions button").forEach(b =>
  b.addEventListener("click", ()=> grade(parseInt(b.dataset.g))));
document.addEventListener("keydown", e=>{
  if (e.code === "Space"){ e.preventDefault(); document.getElementById("deck").click(); }
  else if (e.key === "1") grade(0);
  else if (e.key === "2") grade(3);
  else if (e.key === "3") grade(4);
  else if (e.key === "4") grade(5);
  else if (e.key.toLowerCase() === "r"){ state = {}; localStorage.removeItem(KEY); buildQueue(); }
});
buildQueue();
</script>
</body>
</html>
"""

def main():
    data = json.loads((OUT / "cards.json").read_text(encoding="utf-8"))
    html = TEMPLATE.replace("__CARDS_JSON__", json.dumps(data, ensure_ascii=False))
    (OUT / "review.html").write_text(html, encoding="utf-8")
    print(f"[build_review_html] {len(data['cards'])} cards -> out/review.html")

if __name__ == "__main__":
    main()
