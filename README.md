# 📖 book-to-garden

> 把你的读书笔记，一键变成 **精美 HTML 阅读页 + Anki 卡片 + 翻牌复习站 + 数字花园**。

<p align="center">
  <a href="https://tom61-bl.github.io/book-to-garden/"><strong>✨ 在线 Demo（点我直接体验）</strong></a>
  &nbsp;·&nbsp;
  <a href="https://tom61-bl.github.io/book-to-garden/review.html">翻牌复习</a>
  &nbsp;·&nbsp;
  <a href="https://github.com/tom61-bl/book-to-garden">GitHub</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.10+-yellow.svg" alt="Python">
  <img src="https://img.shields.io/badge/built--with-Quartz-pink.svg" alt="Quartz">
  <img src="https://img.shields.io/badge/Anki-SM--2-green.svg" alt="Anki">
</p>

---

## 它能做什么

把一份 Markdown 笔记丢进去，自动产出 **四样东西**：

| 产物 | 长什么样 | 用途 |
|---|---|---|
| 📖 **精美 HTML 阅读页** | 暖白杂志风、衬线大字、金句高亮、概念折叠、每节小测 | 沉浸式重读 + 提取练习 |
| 🃏 **Anki 卡组 `.apkg`** | 标准 Anki 文件，双击导入 | 长期间隔重复 |
| 🔄 **翻牌复习站** | 深色翻牌 + SM-2 算法 + 进度本地保存 | 网页端快速复习 |
| 🌐 **数字花园网站** | 知识图谱、全文搜索、双链、backlinks | 长期知识管理 |

中间一层"提炼层"自动从笔记标记抽卡：**一次写、多处用**。

## 为什么做这个

普通的读书笔记有三个痛点：

1. **写了不看**——Markdown 堆在 Obsidian 里，再也没打开过；
2. **看了记不住**——没有提取练习，只是被动重读；
3. **记住了不复盘**——没有间隔重复，一周后全忘。

book-to-garden 把这三步串起来：**精美页面让你愿意重读 → 概念折叠+小测逼你提取 → Anki/翻牌站做间隔重复**。

## 快速开始（3 步）

```bash
# 1. 装依赖
pip install -r requirements.txt
cd quartz && npm install && cd ..

# 2. 把你的笔记写进 quartz/content/你的书.md
#    （格式见下文，已有 7 篇《内驱式学习》示例可参考）

# 3. 一键生产
python build.py
```

然后打开：
- 精美阅读页：`tools/out/notes.html`
- 翻牌复习：`tools/out/review.html`
- Anki 卡组：`tools/out/notes.apkg`（双击导入 Anki）
- 数字花园：`cd quartz && npx quartz build --serve`

## 笔记格式

```markdown
---
title: 书名
author: 作者
tags: [book, 主题]
---

# 书名：读书笔记

> [!summary] 一句话精华

### 某个概念
下面这段是解释 —— 自动变成"什么是 X？"问答卡 + 阅读页概念折叠块。

- 问：一个问题？
  答：答案。

> [!quote]
> 金句 —— 自动变成金句卡 + 阅读页大引号高亮。
```

| 写法 | 变成什么 |
|---|---|
| `### 概念名` + 段落 | 问答卡 + 阅读页概念折叠块（提取练习） |
| `- 问：… 答：…` | 问答卡 |
| `> [!quote]` | 金句卡 + 阅读页大引号 |
| `> [!summary]` | 阅读页精华引言 |

卡片 UUID 由"书名+问题"哈希生成，**重复构建不重复**。

## 交互设计（为什么这样做）

阅读页里的两个互动不是装饰，是**认知科学原理的落地**：

- **概念折叠**：默认只露标题，逼你先在脑子里回忆，想不起来再点开——这就是**提取练习（retrieval practice）**，比反复看解释有效得多；
- **每节小测**：读完一个小节立刻做 1 道选择题，选错标粉、选对标绿——这就是**测试效应（testing effect）**，当场验收比事后复习记得牢；
- **翻牌复习站**：用 SM-2 间隔重复算法，根据你的对错自动安排下次复习时间——这就是**分散练习（spaced practice）**。

这些都来自《内驱式学习》这本书本身的理论——**用自己做的工具，复习自己做的笔记**。

## 目录结构

```
├─ quartz/                  # Quartz 数字花园（网站引擎）
│  └─ content/              # ← 你的笔记放这里
├─ tools/
│  ├─ notes_to_cards.py     # 提炼层：笔记 → cards.md + cards.json
│  ├─ build_review_html.py  # → review.html（翻牌复习站）
│  ├─ build_notes_html.py   # → notes.html（杂志风阅读页）
│  └─ out/                  # 产物（git 忽略）
├─ docs/                    # GitHub Pages 部署目录
├─ build.py                 # 一键生产全部
├─ requirements.txt
└─ README.md
```

## 部署到 GitHub Pages

```bash
# 1. 构建并复制到 docs/
python build.py
cp tools/out/notes.html docs/index.html
cp tools/out/review.html docs/review.html

# 2. 提交推送
git add docs/ && git commit -m "deploy" && git push

# 3. 仓库 Settings → Pages → Source 选 master /docs
```

然后访问 `https://<你的用户名>.github.io/<仓库名>/`。

## 致谢

- 网站引擎：[Jacky Zhao / Quartz](https://github.com/jackyzha0/quartz)（MIT）
- Anki 导出：[md2anki](https://pypi.org/project/md2anki/)
- 复习算法：SM-2（可换 FSRS）
- 设计灵感：[zarazhangrui / beautiful-html-templates](https://github.com/zarazhangrui/beautiful-html-templates)

## 贡献

欢迎 PR！常见贡献方向：
- 新的笔记模板（技术书 / 小说 / 论文）
- 新的阅读页主题（深色 / 学术 / 手账风）
- FSRS 算法替换 SM-2
- Obsidian 插件一键导出

## License

MIT
