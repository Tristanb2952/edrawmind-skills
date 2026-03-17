<!-- 开发参考文档 — 不随 SKILL 发布 -->

# Markdown-to-Mindmap HTTP API Reference

> **Endpoint** · `POST /api/ai/mind_agent/skills/markdown_to_mindmap`
> **Content-Type** · `application/json`
> **Timeout** · 120 s (server-side pipeline includes file staging + rendering)

本文档定义 EdrawMind Markdown-to-Mindmap HTTP API 的完整契约。CLI 封装层 `edrawmind_cli.py` 基于此接口实现，二次开发或调试时可直接参考。

---

## 1. 请求

### 1.1 请求头（Headers）

| Header | 必填 | 说明 |
|--------|:----:|------|
| `Content-Type` | ✅ | 固定为 `application/json` |
| `Accept` | ✅ | 固定为 `application/json` |
| `X-API-Key` | 条件 | 当服务端启用 `auth.mode=api_key` 时必填 |
| `Origin` | ❌ | 如传入，需在服务端 `origin_allowlist` 白名单内 |

### 1.2 请求体（Body）

```json
{
  "text":            "# 标题\n## 分支\n- 节点",
  "layout_type":     1,
  "theme_style":     2,
  "background":      "4",
  "line_hand_drawn": false,
  "fill_hand_drawm": "none"
}
```

| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|:----:|------|------|
| `text` | string | ✅ | 非空 | Markdown 文本，服务端仅校验非空；建议客户端做标题/列表预校验 |
| `layout_type` | integer | ❌ | `1`–`12` | 布局类型，默认 `1`（MindMap 双向导图） |
| `theme_style` | integer | ❌ | `1`–`10` | 主题风格，不传则保持导入默认主题 |
| `background` | string | ❌ | 预设 `"1"`–`"15"` 或 `"#RRGGBB"` | 画布背景；自定义颜色优先级高于预设纹理 |
| `line_hand_drawn` | boolean | ❌ | — | 连线手绘风格，默认 `false` |
| `fill_hand_drawm` | string | ❌ | 枚举见下表 | 节点填充手绘风格，默认 `"none"` |

> **注意**：`fill_hand_drawm` 字段名为上游历史拼写（缺少 `n`），保持原样以兼容。

#### `fill_hand_drawm` 枚举值

| 值 | 说明 |
|----|------|
| `"none"` | 标准平面（默认） |
| `"pencil"` | 铅笔素描 |
| `"watercolor"` | 水彩晕染 |
| `"charcoal"` | 木炭素描 |
| `"paint"` | 油漆涂料 |
| `"graffiti"` | 涂鸦网格 |

---

## 2. 响应

### 2.1 成功 — `200 OK`

```json
{
  "code": 0,
  "msg":  "success",
  "data": {
    "file_url":      "https://dev.master.cn/app/editor/{file_id}?from=yiyan",
    "thumbnail_url": "https://mm-dev.edrawsoft.cn/api/mm_web/storage_s3/private/master-img+{file_id}_cover?expire=...&sign=...",
    "extra_info": {
      "elapsed_ms":  962,
      "request_id":  "aaf23d94f8d044e68ba2211213b922c7"
    }
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | `0` 表示成功（部分版本返回 `200`） |
| `msg` | string | 业务消息 |
| `data.file_url` | string | 思维导图在线编辑链接（`http://` 自动规范化为 `https://`） |
| `data.thumbnail_url` | string | 缩略图 URL（带签名和过期时间） |
| `data.extra_info.elapsed_ms` | integer | 服务端端到端耗时（毫秒） |
| `data.extra_info.request_id` | string | 请求唯一标识，用于追踪排障 |

### 2.2 客户端错误 — `400 Bad Request`

```json
{
  "code": 40001,
  "msg":  "text is required",
  "data": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 业务错误码 |
| `msg` | string | 错误描述 |
| `data` | null | 固定为 `null` |

### 2.3 限流 — `429 Too Many Requests`

```json
{
  "code":             "ip_per_day_rate_limited",
  "error":            "rate_limited",
  "message":          "Daily request limit exceeded for this IP",
  "rate_limit_scope": "ip_per_day",
  "retry_after_sec":  60,
  "retryable":        true
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | string | 限流类型：`rate_limited` · `ip_per_day_rate_limited` · `global_per_min_rate_limited` |
| `error` | string | 错误标识 |
| `message` | string | 人类可读描述 |
| `rate_limit_scope` | string | 限流维度：`ip_per_day` · `global_per_min` · `unknown` |
| `retry_after_sec` | integer \| null | 建议等待秒数（可为 `null`） |
| `retryable` | boolean | 是否可重试 |

### 2.4 服务端错误 — `500 Internal Server Error`

结构同 `400`（`code` + `msg` + `data: null`）。

---

## 3. 请求示例

### cURL

```bash
curl -X POST \
  https://dev.master.cn/api/ai/mind_agent/skills/markdown_to_mindmap \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "text": "# Project\n## Frontend\n- React\n- TypeScript\n## Backend\n- Python\n- FastAPI",
    "layout_type": 1,
    "theme_style": 2
  }'
```

### Python (urllib)

```python
import json, urllib.request

payload = json.dumps({
    "text": "# 项目架构\n## 前端\n- React\n## 后端\n- Python",
    "layout_type": 1,
    "theme_style": 2,
}).encode("utf-8")

req = urllib.request.Request(
    "https://dev.master.cn/api/ai/mind_agent/skills/markdown_to_mindmap",
    data=payload,
    headers={"Content-Type": "application/json", "Accept": "application/json"},
    method="POST",
)

with urllib.request.urlopen(req, timeout=120) as resp:
    result = json.loads(resp.read())
    print(result["data"]["file_url"])
```

---

## 4. 错误处理建议

| 场景 | HTTP 状态码 | 推荐处理 |
|------|:-----------:|---------|
| 参数缺失或格式错误 | 400 | 检查 `text` 非空，枚举值合法 |
| API Key 无效或缺失 | 401 / 403 | 检查 `X-API-Key` 头 |
| 限流 | 429 | 读取 `retry_after_sec`，等待后重试 |
| 服务端内部错误 | 500 | 记录 `request_id`，联系服务端团队 |
| SSL 证书错误 | N/A | 开发环境可使用 `--insecure` 跳过验证 |

---

## 5. 备注

- `file_url` 中的 `http://` 地址在服务端返回前自动规范化为 `https://`
- HTTP 接口不内联图片数据，客户端需通过 `thumbnail_url` 自行获取缩略图
- `fill_hand_drawm` 字段拼写为历史遗留问题（缺少末尾 `n`），请保持原样传入

---

*Internal Reference — Wondershare EdrawMind © 2026*
