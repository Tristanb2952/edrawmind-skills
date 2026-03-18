<!-- 开发参考文档 — 不随 SKILL 发布 -->

# Skill CLI 脚本设计指南

> **来源**：`edrawmind_cli.py` 的工程实践总结
> **适用**：后续 Skill 需要接入新 HTTP API 时的脚手架设计参考
> **Last Updated**：2026-03-18

---

## 目录

1. [总体架构](#1-总体架构)
2. [零依赖约束](#2-零依赖约束)
3. [多区域端点选路](#3-多区域端点选路)
4. [异常体系设计](#4-异常体系设计)
5. [失败重试策略](#5-失败重试策略)
6. [输入校验层](#6-输入校验层)
7. [CLI 与 Agent 的输出协议](#7-cli-与-agent-的输出协议)
8. [参数设计规范](#8-参数设计规范)
9. [跨平台兼容](#9-跨平台兼容)
10. [可测试性设计](#10-可测试性设计)
11. [检查清单](#11-检查清单)

---

## 1. 总体架构

采用**单文件 CLI 脚本**架构，职责分层清晰：

```
┌────────────────────────────────────────────────┐
│  CLI Layer (argparse + main)                   │
│  参数解析、输入读取、输出格式化               │
├────────────────────────────────────────────────┤
│  Validation Layer                              │
│  输入内容预校验（可选跳过）                   │
├────────────────────────────────────────────────┤
│  API Client Layer                              │
│  HTTP 请求、响应解析、异常转换                │
├────────────────────────────────────────────────┤
│  Region Layer                                  │
│  端点探测、缓存读写、失败回退                 │
└────────────────────────────────────────────────┘
```

**设计原则：**
- 单文件交付，不拆包——Skill 场景下 agent 需要一个脚本即可运行
- 各层通过函数调用解耦，API Client 可独立于 CLI 使用
- 所有副作用（网络、文件 I/O）集中在最外层，核心逻辑纯函数化

---

## 2. 零依赖约束

Skill 脚本**必须零外部依赖**，只使用 Python 标准库。理由：

- Agent 执行环境不保证有 pip / venv
- 减少安装步骤 = 减少失败概率
- 避免版本冲突影响用户项目

**实践要点：**

| 需求 | 禁用 | 替代方案 |
|------|------|---------|
| HTTP 请求 | `requests` | `urllib.request` + `urllib.error` |
| JSON 处理 | — | `json`（标准库） |
| 并发探测 | `asyncio` / `aiohttp` | `threading` + `socket` |
| 数据模型 | `pydantic` | `dataclasses` + `enum` |
| 颜色输出 | `colorama` / `rich` | 手写 ANSI 转义 + `NO_COLOR` 协议 |
| SSL | `certifi` | `ssl.create_default_context()`（系统证书） |

---

## 3. 多区域端点选路

### 3.1 策略总览

当 API 存在国内/海外多端点时，使用 **TCP 竞速探测 + 本地文件缓存** 方案：

```
用户请求 → 读缓存？
  ├─ 命中且未过期 → 直接使用缓存端点
  └─ 未命中/过期 → 并发 TCP 探测所有端点
                    → 最先连通者胜出
                    → 写入缓存（TTL 24h）
                    → 使用该端点
```

### 3.2 TCP 竞速探测

```python
def _probe_fastest_url() -> str:
    candidates = [
        (CN_URL,     "cn-host.example.com"),
        (GLOBAL_URL, "global-host.example.com"),
    ]
    # 每个候选起一个 daemon 线程，socket.create_connection 到 443 端口
    # 第一个连通的写入 winner，通过 threading.Event 通知主线程
    # 超时或全部失败 → fallback 默认端点
```

**关键参数：**

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `PROBE_TIMEOUT` | 3s | 单次 TCP 连接超时 |
| `Event.wait(timeout)` | `PROBE_TIMEOUT + 1` | 主线程最大等待 |
| fallback | 国内端点 | 全部探测失败时的默认值 |

**为什么用 TCP 而非 HTTP：**
- TCP `connect` 到 443 端口只需 1 个 RTT，极快（通常 <100ms）
- 不消耗服务端 API 资源
- 不需要关心 TLS 握手或 HTTP 响应格式
- 目的纯粹：判断"网络层可达性"，用于选路

### 3.3 本地文件缓存

```json
// 存储路径: {平台缓存目录}/edrawmind/region.json
{"url": "https://...", "ts": 1773836604.71}
```

**缓存读写规则：**
- 读：文件不存在或 `time.time() - ts > TTL` → 视为未命中
- 写：探测完成后写入；所有异常静默忽略（不影响主流程）
- 清除：API 调用失败时主动清除（见第 5 节）
- 全部操作包裹在 `try/except Exception: pass` 中——缓存是加速，不是依赖

### 3.4 用户强制覆盖

始终提供 `--region {auto|cn|global}` 和 `--api-url URL` 参数，优先级：

```
--api-url > --region cn/global > --region auto (默认)
```

这保证了用户在任何网络环境下都有兜底手段。

---

## 4. 异常体系设计

### 4.1 三层异常继承

```
Exception
  └── EdrawMindError          ← 基类：连接超时、DNS 失败、响应格式异常
        └── APIError          ← 服务端返回业务错误 (4xx / 5xx)
              └── RateLimitError  ← 429 限流（携带 retry_after 信息）
```

**这个继承结构对 except 链的路由至关重要。** Python 按声明顺序匹配 except 分支，子类必须先于父类：

```python
try:
    result = call_api(...)
except RateLimitError:    # 最具体 → 先匹配
    handle_rate_limit()
except APIError:          # 次具体 → 4xx/5xx
    handle_api_error()
except EdrawMindError:    # 最泛 → 连接类错误（仅此触发重试）
    handle_connection_error()
```

### 4.2 HTTP 错误解析

`urllib.error.HTTPError` → 读取 response body → 按 HTTP 状态码分发：

```python
def _raise_from_http_error(exc: HTTPError) -> NoReturn:
    body = json.loads(exc.read().decode("utf-8"))
    if exc.code == 429:
        raise RateLimitError(
            code=body.get("code"),
            message=body.get("message"),
            retry_after=body.get("retry_after_sec"),
        )
    raise APIError(exc.code, body.get("code"), body.get("msg"))
```

**要点：**
- body 解析失败时用 HTTP status + reason 兜底
- `RateLimitError` 额外携带 `retry_after` 秒数，方便调用方决策
- 业务成功码兼容多种格式（`code == 0` 或 `code == 200` 或 `code` 不存在）

---

## 5. 失败重试策略

### 5.1 重试条件矩阵

| 异常类型 | auto 模式 | cn/global/api-url 模式 |
|---------|-----------|----------------------|
| `EdrawMindError`（连接失败） | **重试一次** | 直接失败 |
| `APIError`（4xx/5xx） | 直接失败 | 直接失败 |
| `RateLimitError`（429） | 直接失败 | 直接失败 |

**核心逻辑：** 只有在 auto 模式下遇到**连接类错误**才重试，因为这说明缓存的端点可能已失效。API 业务错误和限流说明端点可达，重试同一请求没有意义。

### 5.2 重试流程

```
首次调用失败 (EdrawMindError + is_auto)
  → _warn("Connection failed (...), re-probing endpoints …")
  → _clear_region_cache()      # 删除缓存文件
  → _resolve_api_url()         # 重新 TCP 竞速探测
  → _call_api(new_url)         # 用新端点重试
  → 成功 → 正常输出
  → 再次失败 → _die() 退出
```

### 5.3 最大重试次数

固定为 **1 次**。理由：
- 两个端点都不可达 → 大概率是用户网络问题，再试没用
- 避免 agent 陷入重试循环浪费时间
- 一次重试已足够覆盖"缓存过期指向故障端点"这个主要失败场景

---

## 6. 输入校验层

### 6.1 校验即警告，严重时阻断

```python
def validate(text: str) -> list[str]:
    warnings = []
    # 检查：非空、有标题、有列表项、节点数量
    return warnings

# 调用方决定哪些警告触发阻断
if any("heading" in w.lower() or "empty" in w.lower() for w in warnings):
    die("...")  # 结构性错误 → 阻断
# 其余（如节点过多）→ 仅打印警告，继续执行
```

**设计要点：**
- 校验函数只返回警告列表，**不自行决定是否退出**
- 调用方（main）根据警告类型决定行为
- 提供 `--no-validate` 跳过校验——agent 可能已自行保证输入格式

### 6.2 校验前置于 API 调用

校验发生在 HTTP 请求之前，避免无效内容浪费 API 调用配额和网络时间。

---

## 7. CLI 与 Agent 的输出协议

### 7.1 双通道输出

```
stdout → 机器可解析的结构化数据（URL 或 JSON）
stderr → 人类可读的状态信息（进度、警告、错误）
```

这允许 agent 通过 `stdout` 精确提取结果，同时 `stderr` 的装饰性输出不干扰管道。

### 7.2 输出模式矩阵

| 模式 | stdout | stderr |
|------|--------|--------|
| 默认 | `file_url` | 完整结果（✓、URL、缩略图、耗时） |
| `--quiet` | `file_url` | 无 |
| `--json` | 完整 JSON | 发送进度 |

### 7.3 ANSI 颜色

遵循 [NO_COLOR](https://no-color.org/) 协议：

```python
_on = sys.stderr.isatty() and os.getenv("NO_COLOR") is None
```

- TTY 环境 → 彩色输出
- 管道/重定向/CI → 自动禁用颜色
- 用户设置 `NO_COLOR=1` → 强制禁用

### 7.4 成功/失败标志

agent 通过以下固定字符串判断结果：

| 标志 | 含义 |
|------|------|
| `✓ Mind map generated successfully!` | 成功 |
| `✗` | 失败 |
| `⚠` | 警告（非致命） |

这些字符串是 agent 与 CLI 之间的**隐式契约**，修改时需同步更新 SKILL.md。

---

## 8. 参数设计规范

### 8.1 参数分组

将 argparse 参数按用途分组，提升 `--help` 可读性：

```python
style = parser.add_argument_group("styling options")
conn  = parser.add_argument_group("connection options")
out   = parser.add_argument_group("output options")
```

### 8.2 输入方式：`--text` 优先

| 方式 | 优先级 | 说明 |
|------|--------|------|
| `--text MARKDOWN` | 推荐 | 内联传入，换行用 `\n`；agent 无需创建临时文件 |
| `FILE` | 次选 | 文件路径 |
| `-` | 兜底 | stdin 管道 |

`--text` 和 `FILE` 互斥——在 main 中显式检查，而非用 argparse 的 `mutually_exclusive_group`（因为两者一个是 positional 一个是 optional，原生互斥组不支持）。

### 8.3 枚举参数校验

- 整数范围用 `choices=range(1, 13)`
- 字符串枚举用 `choices=[s.value for s in SomeEnum]`
- 复合格式（如 background 1–15 或 #RRGGBB）用自定义 `type` 函数：

```python
def _validate_background(value: str) -> str:
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value
    if value.isdigit() and 1 <= int(value) <= 15:
        return value
    raise argparse.ArgumentTypeError(f"Invalid: {value}")
```

### 8.4 `None` 语义

可选参数未传入时保持 `None`，**不发送给 API**。这让服务端使用自身默认值，避免客户端与服务端默认值不一致问题：

```python
body = {"text": text}
if layout_type is not None:
    body["layout_type"] = layout_type
# layout_type 为 None → body 中不包含该字段
```

---

## 9. 跨平台兼容

### 9.1 缓存目录

```python
if sys.platform == "win32":
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
elif sys.platform == "darwin":
    base = Path.home() / "Library" / "Caches"
else:
    base = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
return base / "your-tool-name"
```

### 9.2 编码

- 文件读写统一 `encoding="utf-8"`
- JSON payload 用 `ensure_ascii=False` 保留中文原文（减少传输体积）
- HTTP 响应以 `resp.read().decode("utf-8")` 解码

### 9.3 路径

- 一律使用 `pathlib.Path`，不用 `os.path.join`
- 缓存目录创建用 `mkdir(parents=True, exist_ok=True)`

---

## 10. 可测试性设计

### 10.1 main 接受 argv 参数

```python
def main(argv: Sequence[str] | None = None) -> int:
    parser.parse_args(argv)  # argv=None → 使用 sys.argv
```

这允许在单元测试中直接传入参数列表，无需 mock `sys.argv`。

### 10.2 API client 函数独立于 CLI

`markdown_to_mindmap()` 是纯函数式 API client，不依赖 argparse 或全局状态，可独立导入和测试：

```python
from edrawmind_cli import markdown_to_mindmap, MindmapResult
result = markdown_to_mindmap("# Test\n## A\n- B", layout_type=1)
```

### 10.3 验证策略分支

模拟不同场景验证所有代码路径：

| Case | 方法 | 验证目标 |
|------|------|---------|
| 缓存命中 + 正常 | 写入正确缓存 → 运行 | 无 ⚠、无 Retrying |
| 缓存坏端点 | 写入假域名缓存 → 运行 | 触发 ⚠ → Retrying → ✓ |
| 强制模式失败 | `--api-url 假域名` | 直接 ✗，无重试 |
| 无缓存首次 | 删除缓存文件 → 运行 | 自动探测成功 |
| 缓存更新 | 运行后读缓存文件 | URL 和 ts 正确 |
| 异常路由 | 模拟异常 dispatch | RateLimitError/APIError 不入重试分支 |

---

## 11. 检查清单

新接入一个 API Skill 脚本时，逐项对照：

### 基础

- [ ] 单文件、零外部依赖、Python 3.10+ 标准库
- [ ] 文件首行 `#!/usr/bin/env python3`
- [ ] 模块级 docstring 包含用法示例
- [ ] `__version__` 常量

### 输入

- [ ] 支持 `--text` 内联输入（agent 首选）
- [ ] 支持文件路径和 stdin (`-`)
- [ ] 输入校验在 API 调用之前
- [ ] 提供 `--no-validate` 跳过校验

### 网络

- [ ] 使用 `urllib.request`，不引入 `requests`
- [ ] HTTPS + 系统证书；`--insecure` 仅用于开发
- [ ] 合理的请求超时（推荐 60–120s）
- [ ] 多端点场景实现竞速探测 + 本地缓存
- [ ] 缓存读写异常静默处理，不阻断主流程

### 异常

- [ ] 三层异常继承：`Base → APIError → RateLimitError`
- [ ] except 链按子类→父类顺序排列
- [ ] 连接类错误在 auto 模式下触发清缓存 + 重试一次
- [ ] API 业务错误和限流不触发重试

### 输出

- [ ] stdout: 机器可读（URL 或 JSON）
- [ ] stderr: 人类可读（状态、进度、错误）
- [ ] ANSI 颜色遵循 NO_COLOR 协议
- [ ] 固定的成功/失败标志字符串（与 SKILL.md 保持一致）
- [ ] `--json` / `--quiet` 模式可选

### 参数

- [ ] 分组：styling / connection / output
- [ ] 可选参数未传入时为 `None`，不发送给 API
- [ ] 枚举参数使用 `choices` 或自定义 `type` 校验
- [ ] `--region` 支持 auto / cn / global
- [ ] `--api-url` 覆盖一切

### 跨平台

- [ ] 缓存目录适配 Win / macOS / Linux
- [ ] 文件 I/O 统一 UTF-8 编码
- [ ] 使用 `pathlib.Path`

---

*Internal Reference — Wondershare EdrawMind © 2026*
