# EdrawMind 思维导图 AI 技能（EdrawMind Mindmap Skill）

> **作者：** EdrawMind AI Team（万兴脑图 AI 团队）· **组织：** Wondershare EdrawMind（万兴脑图）  
> **版本：** 1.0.0 · **许可证：** 专有软件 © 2026 Wondershare EdrawMind（万兴脑图）。保留所有权利。

这是一个面向 AI Agent（如 OpenClaw、GitHub Copilot、Claude Code 等）的 AI 技能（Skill），通过 MCP 工具 `markdown_to_mindmap`，将自然语言主题或 Markdown 文档一键转化为专业思维导图。

---

## 技能简介

`edrawmind-mindmap` 技能让您用结构化的 Markdown 内容生成专业思维导图。生成后会返回在线编辑链接和缩略图预览，可在 **EdrawMind**（万兴脑图）网页端打开编辑，也可导出为 `.emmx` 格式在桌面端使用。

### 适用场景

- 大纲与提纲
- 会议纪要
- 学习笔记与知识整理
- 项目规划与任务拆解
- 读书笔记与知识框架
- 代码架构可视化

### 解决什么问题

- **无需设计能力** — 只需准备结构化的 Markdown 文本，AI 自动完成布局与渲染，即使不懂绘图工具也能产出专业思维导图。
- **即时在线预览** — 生成后返回在线编辑链接和缩略图，可直接查看和编辑。
- **可导出编辑** — 生成的思维导图可导出为 `.emmx` 格式，在 EdrawMind 桌面端进行二次编辑。

---

## 安装方法

将本仓库的 `skills/edrawmind-mindmap` 目录添加到您的 AI Agent 技能目录中即可。

---

## 快速开始

### 触发方式

在 AI Agent 对话中，用自然语言描述需求，技能将自动激活：

- *"帮我生成一张关于机器学习知识体系的思维导图"*
- *"把这份 Markdown 文档转成思维导图"*
- *"创建一个项目架构的脑图"*

### MCP 工具调用

**工具名称：** `markdown_to_mindmap`

**参数：**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | string | 是 | 合法的 Markdown 文本。必须包含至少一个一级或二级标题（`#` 或 `##`），以及至少一个列表项（`-`、`*`、`+` 或 `1.`）。不能是纯文本散文。 |

### Markdown 输入要求

- 必须包含至少一个一级或二级标题（`#` 或 `##`）
- 必须包含至少一个列表项（`-`、`*`、`+` 或 `1.`）
- 使用 `#` 表示根节点/中心主题，`##` 表示一级分支，`###` 表示二级分支
- 使用 `-` 列表项表示子节点，缩进列表项表示更深层子节点
- 节点文字保持简洁（中文建议 3-10 个字）
- 建议最大深度 4-5 层，最大节点数约 80 个

**输入示例：**

```markdown
# 项目架构
## 前端
- React
- TypeScript
## 后端
- Python
- FastAPI
## 数据库
- PostgreSQL
- Redis
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

| 字段 | 类型 | 说明 |
|---|---|---|
| `file_url` | string | 思维导图在线编辑链接，**必须展示给用户** |
| `thumbnail_url` | string | 封面缩略图 URL |
| `extra_info.elapsed_ms` | number | 服务端生成耗时（毫秒） |
| `extra_info.request_id` | string | 请求唯一标识 |

此外，工具还会返回一个图片内容块，包含思维导图的预览缩略图，支持在聊天界面中直接展示。

---

## 注意事项

- 内容必须结构化：纯文本段落无法正确生成思维导图，必须使用标题和列表组织内容
- 一级标题作为根节点：`# 标题` 会成为思维导图的中心主题，建议每次只使用一个一级标题
- 层级不宜过深：建议控制在 4-5 层以内
- 对于大型文档（100+ 个标题），考虑按顶级章节拆分为多个思维导图
- **必须向用户展示返回的 `file_url`**，确保用户能够访问和编辑生成的思维导图
- 支持图片渲染时应直接展示返回的缩略图

---

## 版权声明

© 2026 Wondershare EdrawMind（万兴脑图）AI Team。保留所有权利。

本技能及所有相关资源均为万兴脑图 Wondershare EdrawMind 的专有财产。未经书面授权，严禁复制、修改、分发或反向工程。

完整许可条款见 [`skills/edrawmind-mindmap/license.txt`](skills/edrawmind-mindmap/license.txt)。

---

## 常见问题（FAQ）

**Q：使用 EdrawMind 思维导图技能是否需要付费？**  
A：目前为限时免费，用户可免费调用思维导图生成服务。

**Q：生成的思维导图支持哪些输出格式？**  
A：生成后返回在线编辑链接和缩略图预览。可在 EdrawMind 网页端直接编辑，也可导出为 `.emmx` 格式在桌面端使用。

**Q：我的数据安全吗？**  
A：Markdown 内容通过 HTTPS 加密传输。请勿在内容中包含敏感信息或个人隐私数据。

**Q：如何反馈问题或建议新功能？**  
A：请发送邮件至 📧 **ws-business@wondershare.cn**，描述您遇到的问题或希望增加的功能，我们将尽快回复。
