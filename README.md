# 📚 book-to-garden · 读书笔记 → 精美网站 + Anki 卡片

把一本书的零散笔记，自动变成三样东西：

1. **精美数字花园网站**（基于 [Quartz](https://github.com/jackyzha0/quartz)）——知识图谱、全文搜索、双链、暗色模式；
2. **Anki 卡组 `.apkg`**（基于 [md2anki](https://pypi.org/project/md2anki/)）——双击导进 Anki 即可间隔重复；
3. **网页复习卡 `review.html`**——双击即用，翻牌交互 + SM-2 间隔重复 + 进度存本地，不依赖 Anki。

中间加了一层"提炼层"：自动从笔记里的 `### 概念`、`- 问：…答：…`、`> [!quote]` 标记抽成卡片，一次写、三处用。

## 快速开始

```powershell
# 1. 装依赖（Quartz 站点）
cd quartz
npm install

# 2. 放笔记：把 .md 写进 quartz/content/ （格式见下文）

# 3. 生成卡片 + Anki 文件 + 网页复习卡
cd ..\tools
python notes_to_cards.py
md2anki out/cards.md -o-anki out/notes.apkg
python build_review_html.py

# 4. 本地预览网站
cd ..\quartz
npx quartz build --serve        # 打开 http://localhost:8080
```

- **看网站**：`quartz/public/` 即成品，推到 GitHub Pages 即可公开。
- **背卡片**：双击 `tools/out/review.html`（空格翻面，1~4 评分）。
- **导 Anki**：双击 `tools/out/notes.apkg`。

## 笔记怎么写（放进 `quartz/content/你的书.md`）

```markdown
---
title: 书名
author: 作者
tags: [book, 主题]
---

# 书名：读书笔记

> [!summary] 一句话精华
> 全书最核心的那句话。

### 某个概念
下面这段是这个概念的解释 —— 自动变成"什么是 X？"卡片。

- 问：直接写一个问题？
  答：这是答案。

> [!quote]
> 这是金句 —— 自动变成金句卡。
```

支持三种自动标记：
| 写法 | 变成什么卡 |
|---|---|
| `### 概念名` + 下方段落 | "什么是概念名？" 问答卡 |
| `- 问：… 答：…` | 问答卡 |
| `> [!quote]` | 金句卡 |

卡片 UUID 由"书名+问题"哈希生成，重复跑脚本不会产生重复卡。

## 目录结构

```
├─ quartz/            # Quartz 5（数字花园引擎）
│  ├─ content/        # ← 你的读书笔记
│  └─ quartz.config.yaml
├─ tools/
│  ├─ notes_to_cards.py     # 提炼层：笔记 → cards.md + cards.json
│  ├─ build_review_html.py   # cards.json → review.html
│  └─ out/                  # 产物（git 忽略）
└─ README.md
```

## 致谢
- 网站：[Jacky Zhao / Quartz](https://github.com/jackyzha0/quartz)（MIT）
- Anki 导出：[md2anki](https://pypi.org/project/md2anki/)
- 复习算法：简化版 SM-2（可换成 [FSRS](https://open-spaced-repetition.github.io/awesome-fsrs/)）

## License
MIT
