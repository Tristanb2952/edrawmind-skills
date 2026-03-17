# EdrawMind 思维导图 AI 技能

> **作者：** EdrawMind AI Team（万兴脑图 AI 团队）· **组织：** Wondershare EdrawMind（万兴脑图）
> **版本：** 1.0.0 · **许可证：** 专有软件 © 2026 Wondershare EdrawMind。保留所有权利。

[English](README.md)

面向 AI Agent（GitHub Copilot、Claude Code 等）的 AI 技能，通过 Markdown 内容生成专业思维导图。支持自定义布局、主题、背景和手绘风格。

---

## 技能简介

`edrawmind-mindmap` 技能通过 EdrawMind HTTP API 将结构化 Markdown 转化为专业思维导图。支持 12 种布局、10 种主题、15 种背景预设和多种手绘效果。

### 适用场景

- 大纲与提纲
- 会议纪要与学习笔记
- 项目规划与任务拆解
- 代码架构可视化
- 知识框架与读书笔记

### 解决什么问题

- **无需设计能力** — 只需准备 Markdown 文本，AI 自动完成布局与渲染。
- **丰富的定制选项** — 12 种布局（思维导图、时间线、鱼骨图、组织架构图等）、10 种主题和手绘风格。
- **即时在线预览** — 生成后返回在线编辑链接和缩略图，可直接查看和编辑。

---

## 项目结构

```
edrawmind-skills/
├── pyproject.toml                  # 项目配置（uv / pip）
├── scripts/
│   └── build.py                    # 构建脚本 — 打包技能为 zip
├── skills/
│   └── edrawmind-mindmap/          # 技能目录
│       ├── SKILL.md                # 技能定义（Agent 读取此文件）
│       ├── license.txt
│       ├── docs/                   # 内部开发文档（不包含在 zip 中）
│       ├── references/             # 参考文档（按需加载）
│       │   ├── markdown-format.md
│       │   ├── style-guide.md
│       │   └── tool-reference.md
│       └── scripts/
│           └── edrawmind_cli.py    # HTTP API 命令行工具
├── README.md
└── README_CN.md
```

---

## 安装方法

### 从发布包安装

1. 从 [Releases](../../releases) 下载 `edrawmind-mindmap.zip`
2. 解压到 AI Agent 技能目录：
   - **GitHub Copilot**：`.github/skills/`
   - **Claude Code**：`.claude/skills/`
   - **通用**：`.agents/skills/`

### 从源码安装

```bash
git clone <repo-url>
cd edrawmind-skills
```

---

## 构建

将技能打包为可分发的 zip 文件（不含 `docs/`）：

```bash
# 使用 uv
uv run python scripts/build.py

# 或直接运行
python scripts/build.py

# 自定义输出路径
python scripts/build.py -o dist/custom-name.zip

# 仅列出文件（不打包）
python scripts/build.py --list
```

输出位置：`dist/edrawmind-mindmap.zip`

---

## 快速开始

### 触发方式

在 AI Agent 对话中，用自然语言描述需求，技能将自动激活：

- *"帮我生成一张关于机器学习知识体系的思维导图"*
- *"把这份 Markdown 文档转成思维导图"*
- *"创建一个项目架构的脑图"*

### CLI 工具

技能通过 `edrawmind_cli.py` 调用 EdrawMind HTTP API：

```bash
# 基本用法
python edrawmind_cli.py input.md

# 指定布局、主题和背景
python edrawmind_cli.py --layout 7 --theme 9 --background 4 timeline.md

# 手绘风格
python edrawmind_cli.py --line-hand-drawn --fill pencil --background 9 notes.md
```

### 返回数据

```json
{
  "file_url": "https://...",
  "thumbnail_url": "https://...",
  "extra_info": {
    "elapsed_ms": 962,
    "request_id": "aaf23d94f8d044e68ba2211213b922c7"
  }
}
```

| 字段 | 说明 |
|---|---|
| `file_url` | 在线编辑链接，**必须展示给用户** |
| `thumbnail_url` | 封面缩略图 URL |

---

## 样式选项

| 参数 | 取值范围 | 说明 |
|------|----------|------|
| `--layout N` | 1–12 | 布局类型（思维导图、时间线、鱼骨图、组织架构图等） |
| `--theme N` | 1–10 | 主题风格（默认、知识、鲜明、简约等） |
| `--background BG` | 1–15 或 `#RRGGBB` | 画布背景 |
| `--line-hand-drawn` | 标志位 | 手绘连接线 |
| `--fill STYLE` | none/pencil/watercolor/charcoal/paint/graffiti | 节点填充风格 |

详细参数说明见 [style-guide.md](skills/edrawmind-mindmap/references/style-guide.md)。

---

## 注意事项

- 内容必须是结构化 Markdown，包含标题和列表
- 使用一个 `#` 标题作为根节点
- 建议最大深度 5 层，约 80 个节点
- 大型文档（100+ 个标题）建议按章节拆分
- **务必向用户展示返回的 `file_url`**

---

## 版权声明

© 2026 Wondershare EdrawMind（万兴脑图）AI Team。保留所有权利。

完整许可条款见 [`skills/edrawmind-mindmap/license.txt`](skills/edrawmind-mindmap/license.txt)。

---

## 常见问题

**Q：使用 EdrawMind 思维导图技能是否需要付费？**
A：目前为限时免费，用户可免费调用思维导图生成服务。

**Q：生成的思维导图支持哪些输出格式？**
A：生成后返回在线编辑链接和缩略图预览。可在 EdrawMind 网页端直接编辑，也可导出为 `.emmx` 格式在桌面端使用。

**Q：我的数据安全吗？**
A：Markdown 内容通过 HTTPS 加密传输。请勿在内容中包含敏感信息或个人隐私数据。

**Q：如何反馈问题或建议新功能？**
A：请发送邮件至 📧 **ws-business@wondershare.cn**
