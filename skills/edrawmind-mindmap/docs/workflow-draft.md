<!-- 开发参考文档 — 不随 SKILL 发布 -->

# Markdown-to-Mindmap 生成流程参考

> **Version** 1.0 · **Last Updated** 2026-03-17
> **Owner** EdrawMind AI Team · **Status** Active

本文档描述从用户输入到思维导图生成的完整处理流程，供开发团队理解系统行为和排障参考。

---

## 1. 端到端流程总览

```mermaid
flowchart TD
    A([用户输入]) --> B{输入类型判断}

    B -->|已有 Markdown 文件| C[读取文件内容]
    B -->|自然语言主题描述| D[生成 Markdown 大纲]
    B -->|代码库/项目结构| E[探索代码库并整理结构]

    C --> F[内容清洗与标准化]
    D --> F
    E --> F

    F --> G[Markdown 校验]
    G -->|校验失败| G1([提示用户修正])
    G -->|校验通过| H[参数推断与确定]

    H --> H1[布局类型 layout_type]
    H --> H2[主题风格 theme_style]
    H --> H3[画布背景 background]
    H --> H4[手绘风格 hand_drawn]

    H1 & H2 & H3 & H4 --> I[组装 CLI 命令]
    I --> J[执行 edrawmind_cli.py]
    J --> K[HTTP POST API 调用]

    K --> L{响应状态}
    L -->|200 OK| M[解析 file_url + thumbnail_url]
    L -->|429 限流| N[等待 retry_after_sec 后重试]
    L -->|4xx / 5xx| O([输出错误信息])

    M --> P[向用户展示结果]
    P --> P1[展示在线编辑链接]
    P --> P2[展示缩略图预览]
```

---

## 2. 内容准备阶段

### 2.1 输入来源

| 来源 | 处理策略 |
|------|---------|
| Markdown 文件 | 直接读取 → 内容清洗 |
| 自然语言描述 | 根据主题生成 2–4 层 Markdown 大纲 |
| 代码库/项目结构 | 遍历目录树 → 按模块整理为 Markdown 层级 |

### 2.2 内容清洗规则

```mermaid
flowchart LR
    A[原始内容] --> B[去除编号前缀]
    B --> C[精简冗长标题]
    C --> D[确保单根节点]
    D --> E[控制深度 ≤ 5 层]
    E --> F[控制节点 ≤ 80 个]
    F --> G[标准化 Markdown]
```

- **去除编号前缀**：`## 3.1 设计原则` → `## 设计原则`
- **精简标题**：节点文字中文 3–10 字，英文 3–5 词
- **单根节点**：仅保留一个 `#` 一级标题作为根节点
- **深度控制**：超过 5 层时尝试合并/拍平叶子节点
- **数量控制**：超过 80 节点时建议按章节拆分

### 2.3 校验规则

| 检查项 | 条件 | 失败行为 |
|--------|------|---------|
| 非空检查 | `text` 不为空 | 拒绝并提示 |
| 标题检查 | 至少包含一个 `#` 或 `##` 标题 | 拒绝并提示 |
| 列表检查 | 至少包含一个列表项（`-`/`*`/`+`/`1.`） | 拒绝并提示 |
| 数量预警 | 节点数 > 80 | 警告（不阻断） |

---

## 3. 参数推断阶段

当用户未显式指定样式参数时，系统根据内容语义自动推断。用户显式指定的参数始终优先。

### 3.1 推断决策树

```mermaid
flowchart TD
    A{用户是否指定?} -->|是| B([使用用户指定值])
    A -->|否| C{内容关键词分析}

    C --> D1["含 时间/进度/里程碑"]
    C --> D2["含 组织/部门/团队"]
    C --> D3["含 原因/根因/6M"]
    C --> D4["含 对比/SWOT/矩阵"]
    C --> D5["含 清单/目录/大纲"]
    C --> D6["其他/通用"]

    D1 --> E1["layout=7 (时间轴)"]
    D2 --> E2["layout=5 (组织结构图)"]
    D3 --> E3["layout=8 (鱼骨图)"]
    D4 --> E4["layout=12 (矩阵图)"]
    D5 --> E5["layout=10 (括号图)"]
    D6 --> E6["layout=1 (MindMap)"]
```

### 3.2 参数搭配示例

| 场景 | `layout_type` | `theme_style` | `background` | 手绘 |
|------|:---:|:---:|:---:|------|
| 学习笔记 | 1 | 2 (Knowledge) | — | — |
| 项目里程碑 | 7 (Timeline) | 4 (Minimal) | 4 (晴空蓝) | — |
| 头脑风暴 | 1 | 5 (Rainbow) | — | — |
| 手绘素描 | 1 | 6 (Paper) | 9 (棉纸纹) | line + pencil |
| 技术架构 | 3 (RightTree) | 10 (SciFi) | 8 (碳黑) | — |
| 组织架构 | 5 (OrgDown) | 4 (Minimal) | 3 (暖奶白) | — |

---

## 4. 调用执行阶段

### 4.1 CLI 调用链路

```mermaid
sequenceDiagram
    participant Agent as AI Agent
    participant CLI as edrawmind_cli.py
    participant API as HTTP API Server

    Agent->>Agent: 写入 Markdown 到临时文件
    Agent->>CLI: python edrawmind_cli.py [options] file.md
    CLI->>CLI: 读取文件 & 校验 Markdown
    CLI->>API: POST /markdown_to_mindmap (JSON Body)
    API->>API: Markdown 解析 → 导图渲染 → 文件上传

    alt 200 OK
        API-->>CLI: {code:0, data:{file_url, thumbnail_url, extra_info}}
        CLI-->>Agent: stdout 输出 file_url
    else 429 Rate Limited
        API-->>CLI: {code, retry_after_sec}
        CLI-->>Agent: 退出码 1 + 限流提示
    else 4xx / 5xx
        API-->>CLI: {code, msg}
        CLI-->>Agent: 退出码 1 + 错误信息
    end

    Agent->>Agent: 向用户展示 file_url + thumbnail_url
```

### 4.2 CLI 参数与 API 字段映射

| CLI 参数 | API 字段 | 类型 | 约束 |
|---------|---------|------|------|
| `--layout N` | `layout_type` | int | 1–12 |
| `--theme N` | `theme_style` | int | 1–10 |
| `--background BG` | `background` | string | 1–15 或 `#RRGGBB` |
| `--line-hand-drawn` | `line_hand_drawn` | bool | — |
| `--fill STYLE` | `fill_hand_drawm` | string | 枚举值 |
| `--api-key KEY` | Header `X-API-Key` | string | — |
| `--insecure` | (SSL context) | — | 跳过证书验证 |

> `fill_hand_drawm` 字段名为上游历史拼写（缺少末尾 `n`），CLI 层自动处理映射。

---

## 5. 结果展示阶段

```mermaid
flowchart LR
    A[CLI 输出] --> B{解析结果}
    B --> C[file_url — 在线编辑链接]
    B --> D[thumbnail_url — 缩略图]
    B --> E[extra_info — 元信息]

    C --> F["**必须展示** 给用户"]
    D --> G["支持图片环境时展示"]
    E --> H["用于调试/日志"]
```

- `file_url` **必须** 展示给用户，这是使用契约的硬性要求
- `thumbnail_url` 在支持图片渲染的环境中展示预览
- `extra_info.request_id` 用于故障排查时关联服务端日志

---

## 6. 异常处理

| 异常类型 | 现象 | 处理策略 |
|---------|------|---------|
| Markdown 校验失败 | 无标题或无列表项 | 提示用户修正格式；可用 `--no-validate` 跳过 |
| SSL 证书错误 | 开发环境自签名证书 | 使用 `--insecure` 跳过验证 |
| HTTP 429 限流 | 请求频率超限 | 读取 `retry_after_sec`，等待后重试 |
| HTTP 500 服务端错误 | 渲染管线异常 | 记录 `request_id`，联系服务端团队 |
| 主题+布局兼容问题 | 部分组合偶发保存失败 | 更换主题编号后重试 |
| 网络连接失败 | DNS 解析或网络不可达 | 检查网络连通性和 API 端点地址 |

---

## 7. 架构边界

```mermaid
C4Context
    title Markdown-to-Mindmap 系统边界

    Person(user, "用户")
    System(agent, "AI Agent", "Copilot / Chat")
    System(cli, "edrawmind_cli.py", "CLI 封装层")
    System_Ext(api, "EdrawMind API", "HTTP 服务")
    System_Ext(storage, "Cloud Storage", "文件 & 缩略图")

    Rel(user, agent, "自然语言描述 / Markdown")
    Rel(agent, cli, "终端调用")
    Rel(cli, api, "POST JSON")
    Rel(api, storage, "上传生成文件")
    Rel(api, cli, "file_url + thumbnail_url")
    Rel(agent, user, "展示链接 + 缩略图")
```

---

*Internal Reference — Wondershare EdrawMind © 2026*
