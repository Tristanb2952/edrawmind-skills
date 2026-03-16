---
name: edrawmind-mindmap
description: "凡是涉及思维导图的任务均使用此技能，包括：创建、生成、或将内容转换为思维导图。具体场景包括：从 Markdown 文档、代码架构、需求文档或任意结构化文本生成思维导图；根据用户描述的主题或大纲创建思维导图。当用户提到"思维导图"、"脑图"、"mindmap"、"mind map"、"导图"，或希望将层级/结构化信息可视化为树状图时，即触发此技能。"
argument-hint: "描述您想创建的思维导图主题，或提供 Markdown 内容"
---

# EdrawMind（万兴脑图）思维导图生成技能

通过 MCP server `edrawmind-mcp` 提供的 `markdown_to_mindmap` 工具，将自然语言主题或已有 Markdown 文档转化为思维导图。生成后返回在线编辑链接和缩略图预览，可在 **EdrawMind**（万兴脑图）网页端打开编辑，也可导出为 `.emmx` 格式在桌面端使用。

## 快速参考

| 任务场景 | 处理方式 |
|---------|---------|
| 从已有 Markdown 文件生成 | 读取文件 → 提取并清理标题 → 调用 MCP 工具 |
| 根据用户描述的主题生成 | 起草 Markdown 大纲 → 调用 MCP 工具 |
| 从代码/项目结构生成 | 探索代码库 → 整理为 Markdown 层级 → 调用 MCP 工具 |

---

## Step 1 — 准备 Markdown 内容

输入必须是**结构良好的 Markdown**，包含标题（`#`/`##`/`###`）和列表项（`-`/`*`/`+`/`1.`）。

**核心要求：**
- 必须包含至少一个一级或二级标题
- 必须包含至少一个列表项
- 不能是纯文本散文
- 节点文字保持简洁，去除编号前缀
- 建议最大深度 4-5 层，最大节点数约 80 个

> 详细格式规范、层级映射关系及示例参见 [Markdown 格式规范](./references/markdown-format.md)。

---

## Step 2 — 调用 MCP 工具

调用 MCP server `edrawmind-mcp` 提供的 `markdown_to_mindmap` 工具，参数如下：

> **注意：** 不同 Agent 平台的工具名称格式可能不同。在 VS Code / GitHub Copilot 中工具名为 `mcp_edrawmind-mcp_markdown_to_mindmap`，在其他平台中通常为 `markdown_to_mindmap`。请根据实际环境中可用的工具名称进行调用。

| 参数 | 类型 | 必填 | 说明 |
|-----|------|:----:|-----|
| `text` | string | ✅ | 合法的 Markdown 文本 |

**返回数据：**

| 字段 | 说明 |
|------|------|
| `file_url` | 思维导图在线编辑链接，**必须展示给用户** |
| `thumbnail_url` | 封面缩略图 URL |

工具还会返回一个图片内容块（预览缩略图），支持在聊天界面中直接展示。

> 完整的工具参数、返回格式及调用示例参见 [工具 API 参考](./references/tool-reference.md)。

---

## Step 3 — 展示结果

1. **必须展示 `file_url`**：提供在线编辑链接，确保用户能访问和编辑思维导图
2. **展示缩略图**：如果当前环境支持图片渲染，直接展示返回的缩略图

---

## 应用场景

### 从已有 Markdown 文档生成

1. 读取源 Markdown 文件
2. 提取标题结构，清理编号前缀、精简冗长标题
3. 调用 `markdown_to_mindmap`
4. 展示 `file_url` 和缩略图

### 根据用户描述的主题生成

1. 获取用户的主题（或从对话中推断）
2. 起草包含 2-4 层深度的 Markdown 大纲（标题 + 列表项）
3. 调用 `markdown_to_mindmap`
4. 展示 `file_url` 和缩略图

### 从代码库/项目结构生成

1. 探索代码库，理解架构
2. 整理为 Markdown 层级结构（标题 + 列表项）
3. 调用 `markdown_to_mindmap`
4. 展示 `file_url` 和缩略图

---

## 注意事项

- 纯文本段落无法生成思维导图，必须使用标题和列表
- 建议每次只使用一个 `#` 一级标题作为根节点
- 对于大型文档（100+ 个标题），按章节拆分为多个思维导图
- **必须向用户展示返回的 `file_url`**

---

© 2026 Wondershare EdrawMind（万兴脑图）. All rights reserved.
