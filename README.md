# 📖 book-to-garden

> 读书笔记 → 精美 HTML 阅读页 + Anki 卡片 + 数字花园网站

把一本书的零散笔记，自动变成三样东西：

1. **精美 HTML 阅读页**（Zara 式极简杂志风，`tools/out/notes.html`）—— 暖白底、衬线大字、大量留白、金句居中高亮；
2. **Anki 卡组 `.apkg`**（基于 [md2anki](https://pypi.org/project/md2anki/)）—— 双击导进 Anki 间隔重复；
3. **网页复习卡 `review.html`**—— 翻牌交互 + SM-2 间隔重复 + 进度存本地；
4. **完整数字花园网站**（基于 [Quartz](https://github.com/jackyzha0/quartz)）—— 知识图谱、全文搜索、双链。

中间一层"提炼层"自动从笔记标记抽卡：一次写、多处用。

## 快速开始

```powershell
# 0. 装依赖（一次性）
cd quartz; npm install; cd ..
pip install -r requirements.txt

# 1. 把读书笔记写进 quartz/content/*.md （格式见下文）

# 2. 一键生产
python build.py

# 3. 看成品
#    精美阅读页：双击 tools/out/notes.html
#    数字花园：  cd quartz; npx quartz build --serve
#    导 Anki：   双击 tools/out/notes.apkg
```

## 笔记格式（写进 quartz/content/你的书.md）

```markdown
---
title: 书名
author: 作者
tags: [book, 主题]
---

# 书名：读书笔记

> [!summary] 一句话精华

### 某个概念
下面这段是解释 —— 自动变成"什么是 X？"卡片。

- 问：一个问题？
  答：答案。

> [!quote]
> 金句 —— 自动变成金句卡。
```

| 写法 | 变成什么 |
|---|---|
| `### 概念名` + 段落 | 问答卡 + 阅读页概念块 |
| `- 问：… 答：…` | 问答卡 |
| `> [!quote]` | 金句卡 + 阅读页大引号 |
| `> [!summary]` | 阅读页精华引言 |

卡片 UUID 由"书名+问题"哈希生成，重复构建不重复。

## 目录

```
├─ quartz/            # Quartz 数字花园
│  └─ content/       # 你的笔记
├─ tools/
│  ├─ notes_to_cards.py     # 提炼：笔记→卡片
│  ├─ build_review_html.py   # → review.html
│  ├─ build_notes_html.py    # → notes.html (Zara风)
│  └─ out/                   # 产物（git 忽略）
├─ build.py                  # 一键生产
├─ requirements.txt
└─ README.md
```

## 致谢
- 网站引擎：[Jacky Zhao / Quartz](https://github.com/jackyzha0/quartz)（MIT）
- Anki 导出：[md2anki](https://pypi.org/project/md2anki/)
- 复习算法：SM-2（可换 FSRS）

## License
MIT
