# edrawmind_cli.py CLI 工具参考

## 一、工具简介

`edrawmind_cli.py` 是一个零依赖的 Python 命令行工具，封装了 EdrawMind（万兴脑图）Markdown-to-Mindmap HTTP API。读取 Markdown 文件或 stdin 输入，生成思维导图，返回在线编辑链接和缩略图预览。

脚本位置：`./scripts/edrawmind_cli.py`

---

## 二、命令格式

```
python edrawmind_cli.py [OPTIONS] <FILE | ->
```

**位置参数：**
- `FILE` — Markdown 文件路径
- `-` — 从 stdin 读取

---

## 三、完整参数说明

### 风格选项

| 选项 | 类型 | 说明 |
|------|------|------|
| `-l, --layout N` | int (1–12) | 布局类型，默认 `1`（MindMap 双向导图） |
| `-t, --theme N` | int (1–10) | 主题风格 |
| `-b, --background BG` | string | 背景：预设 `1`–`15` 或自定义 `"#RRGGBB"` |
| `--line-hand-drawn` | flag | 启用连线手绘风格 |
| `--fill STYLE` | string | 节点填充手绘：`none`/`pencil`/`watercolor`/`charcoal`/`paint`/`graffiti` |

### 连接选项

| 选项 | 说明 |
|------|------|
| `--api-key KEY` | API 密钥（默认取 `$EDRAWMIND_API_KEY`） |
| `--api-url URL` | API 端点 URL（默认取 `$EDRAWMIND_API_URL` 或内置地址） |

### 输出选项

| 选项 | 说明 |
|------|------|
| `-o, --output PATH` | 将 JSON 响应保存到文件 |
| `--json` | 输出完整 JSON 响应到 stdout |
| `-q, --quiet` | 仅输出 file_url（无装饰） |
| `--open` | 在默认浏览器中打开思维导图链接 |
| `--no-validate` | 跳过 Markdown 输入校验 |
| `-V, --version` | 显示版本号 |

---

## 四、返回数据格式

成功时（默认输出）打印 `file_url` 到 stdout，详细信息到 stderr。

使用 `--json` 时输出完整 JSON：

```json
{
  "file_url": "https://dev.master.cn/app/editor/{file_id}?from=yiyan",
  "thumbnail_url": "https://mm-dev.edrawsoft.cn/api/mm_web/storage_s3/...",
  "extra_info": {
    "elapsed_ms": 962,
    "request_id": "aaf23d94f8d044e68ba2211213b922c7"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `file_url` | string | 思维导图在线编辑链接，**必须展示给用户** |
| `thumbnail_url` | string | 封面缩略图 URL（带签名和过期时间） |
| `extra_info.elapsed_ms` | number | 服务端生成耗时（毫秒） |
| `extra_info.request_id` | string | 请求唯一标识 |

---

## 五、错误处理

| 场景 | 行为 |
|------|------|
| Markdown 无标题/列表 | 校验失败退出（使用 `--no-validate` 跳过） |
| HTTP 429 限流 | 输出限流信息及重试等待时间 |
| HTTP 4xx/5xx | 输出 API 错误码和消息 |
| 网络连接失败 | 输出连接失败原因 |

---

## 六、调用示例

```bash
# 基本转换
python edrawmind_cli.py roadmap.md

# 指定布局、主题和背景
python edrawmind_cli.py --layout 7 --theme 9 --background 4 timeline.md

# 手绘素描风格
python edrawmind_cli.py --line-hand-drawn --fill pencil --background 9 notes.md

# 从 stdin 管道输入
echo "# AI\n## ML\n- Deep Learning" | python edrawmind_cli.py -

# 浏览器打开并保存 JSON
python edrawmind_cli.py --open --json -o result.json input.md

# 仅输出 URL（适合管道）
python edrawmind_cli.py -q input.md
```
