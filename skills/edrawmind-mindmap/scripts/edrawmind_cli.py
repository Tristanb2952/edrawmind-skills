#!/usr/bin/env python3
"""
edrawmind-cli — Convert Markdown to professional mind maps.

A zero-dependency command-line tool for the EdrawMind (万兴脑图) Markdown-to-Mindmap
HTTP API. Reads Markdown from files or stdin, generates a mind map, and returns an
online editing URL with a thumbnail preview.

Usage examples:

    # Basic — convert a Markdown file
    python edrawmind_cli.py roadmap.md

    # Pipe from stdin
    echo "# AI\\n## ML\\n- Deep Learning" | python edrawmind_cli.py -

    # Choose layout, theme, and background
    python edrawmind_cli.py --layout 7 --theme 9 --background 4 timeline.md

    # Hand-drawn sketch style
    python edrawmind_cli.py --line-hand-drawn --fill pencil --background 9 notes.md

    # Open result in browser and save JSON response
    python edrawmind_cli.py --open --json -o result.json input.md

Copyright (c) 2026 Wondershare EdrawMind. All rights reserved.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import textwrap
import urllib.error
import urllib.request
import webbrowser
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import NoReturn, Optional, Sequence

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Constants
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

__version__ = "1.0.0"
__author__ = "EdrawMind AI Team"

_DEFAULT_API_URL = (
    "https://mindapi.edrawsoft.cn/api/ai/mind_agent/skills/markdown_to_mindmap"
)
_REQUEST_TIMEOUT = 120  # seconds

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ANSI colors (auto-disabled when output is not a TTY or NO_COLOR is set)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _Color:
    """Minimal ANSI color helper respecting the NO_COLOR convention."""

    _on: bool = sys.stderr.isatty() and os.getenv("NO_COLOR") is None

    @classmethod
    def _w(cls, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if cls._on else text

    # fmt: off
    green  = classmethod(lambda cls, t: cls._w("32", t))      # type: ignore[assignment]
    yellow = classmethod(lambda cls, t: cls._w("33", t))      # type: ignore[assignment]
    red    = classmethod(lambda cls, t: cls._w("1;31", t))     # type: ignore[assignment]
    cyan   = classmethod(lambda cls, t: cls._w("36", t))       # type: ignore[assignment]
    bold   = classmethod(lambda cls, t: cls._w("1", t))        # type: ignore[assignment]
    dim    = classmethod(lambda cls, t: cls._w("2", t))        # type: ignore[assignment]
    # fmt: on


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Data models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class FillStyle(str, Enum):
    """Node fill hand-drawn styles."""

    NONE = "none"
    PENCIL = "pencil"
    WATERCOLOR = "watercolor"
    CHARCOAL = "charcoal"
    PAINT = "paint"
    GRAFFITI = "graffiti"


@dataclass(frozen=True)
class ExtraInfo:
    """Server-side metadata attached to a successful response."""

    elapsed_ms: int
    request_id: str


@dataclass(frozen=True)
class MindmapResult:
    """Parsed successful API response."""

    file_url: str
    thumbnail_url: str
    extra_info: ExtraInfo

    @classmethod
    def from_response(cls, data: dict) -> MindmapResult:
        extra = data.get("extra_info", {})
        return cls(
            file_url=data["file_url"],
            thumbnail_url=data["thumbnail_url"],
            extra_info=ExtraInfo(
                elapsed_ms=extra.get("elapsed_ms", 0),
                request_id=extra.get("request_id", ""),
            ),
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Exceptions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class EdrawMindError(Exception):
    """Base exception for all EdrawMind CLI errors."""


class APIError(EdrawMindError):
    """Raised on non-success API responses (4xx / 5xx)."""

    def __init__(self, status: int, code: str | int, message: str) -> None:
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"HTTP {status} — [{code}] {message}")


class RateLimitError(APIError):
    """Raised specifically on HTTP 429 responses."""

    def __init__(
        self,
        code: str,
        message: str,
        retry_after: int | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(429, code, message)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Markdown validation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_RE_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")


def validate_markdown(text: str) -> list[str]:
    """Return a list of warning strings if *text* may not produce a good mind map."""
    warnings: list[str] = []
    lines = text.strip().splitlines()

    if not lines:
        warnings.append("Input is empty.")
        return warnings

    has_heading = any(ln.lstrip().startswith("#") for ln in lines)
    has_list = any(_RE_LIST_ITEM.match(ln) for ln in lines)

    if not has_heading:
        warnings.append(
            "No Markdown heading found. "
            "At least one heading (# or ##) is required."
        )
    if not has_list:
        warnings.append(
            "No list item found. "
            "At least one list item (-, *, +, or 1.) is required."
        )

    node_count = sum(
        1 for ln in lines if ln.lstrip().startswith("#") or _RE_LIST_ITEM.match(ln)
    )
    if node_count > 80:
        warnings.append(
            f"Found ~{node_count} nodes. "
            "Consider splitting into multiple maps (recommended ≤ 80)."
        )

    return warnings


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  API client
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def markdown_to_mindmap(
    text: str,
    *,
    api_url: str = _DEFAULT_API_URL,
    api_key: str | None = None,
    layout_type: int | None = None,
    theme_style: int | None = None,
    background: str | None = None,
    line_hand_drawn: bool | None = None,
    fill_hand_drawn: str | None = None,
    insecure: bool = False,
) -> MindmapResult:
    """Convert Markdown *text* to a mind map via the EdrawMind HTTP API.

    Parameters
    ----------
    text:
        Structured Markdown. Must contain at least one heading and one list item.
    api_url:
        Full API endpoint URL.
    api_key:
        Optional API key sent as ``X-API-Key``.
    layout_type:
        Layout preset ``1``–``12``.
    theme_style:
        Theme preset ``1``–``10``.
    background:
        Background preset ``"1"``–``"15"`` or ``"#RRGGBB"``.
    line_hand_drawn:
        Whether connection lines use the hand-drawn style.
    fill_hand_drawn:
        Node fill style (``none``/``pencil``/``watercolor``/``charcoal``/``paint``/``graffiti``).

    Returns
    -------
    MindmapResult
        Contains ``file_url``, ``thumbnail_url``, and ``extra_info``.

    Raises
    ------
    EdrawMindError
        On network, validation, or unexpected errors.
    APIError
        On non-success HTTP responses.
    RateLimitError
        On HTTP 429 rate-limit responses.
    """
    body: dict = {"text": text}
    if layout_type is not None:
        body["layout_type"] = layout_type
    if theme_style is not None:
        body["theme_style"] = theme_style
    if background is not None:
        body["background"] = background
    if line_hand_drawn is not None:
        body["line_hand_drawn"] = line_hand_drawn
    if fill_hand_drawn is not None:
        # The upstream API field intentionally uses this spelling.
        body["fill_hand_drawm"] = fill_hand_drawn

    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")

    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-API-Key"] = api_key

    req = urllib.request.Request(
        api_url, data=payload, headers=headers, method="POST"
    )

    ssl_ctx: ssl.SSLContext | None = None
    if insecure:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT, context=ssl_ctx) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        _raise_from_http_error(exc)
    except urllib.error.URLError as exc:
        raise EdrawMindError(f"Connection failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise EdrawMindError(f"Invalid JSON in response: {exc}") from exc

    # The success envelope uses code == 0.
    resp_code = raw.get("code")
    if resp_code not in (0, 200, None):
        raise APIError(200, resp_code, raw.get("msg", "Unknown server error"))

    try:
        data = raw.get("data", raw)
        if not isinstance(data, dict):
            raise EdrawMindError(
                f"Unexpected response: 'data' is not an object (got {type(data).__name__})"
            )
        return MindmapResult.from_response(data)
    except (KeyError, AttributeError, TypeError) as exc:
        raise EdrawMindError(
            f"Unexpected response structure: {exc}"
        ) from exc


def _raise_from_http_error(exc: urllib.error.HTTPError) -> NoReturn:
    """Parse an HTTP error response and raise the appropriate exception."""
    try:
        body = json.loads(exc.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise APIError(exc.code, exc.code, exc.reason or "Unknown error") from exc

    if exc.code == 429:
        raise RateLimitError(
            code=body.get("code", "rate_limited"),
            message=body.get("message", body.get("error", "Rate limited")),
            retry_after=body.get("retry_after_sec"),
        )

    raise APIError(
        exc.code,
        body.get("code", exc.code),
        body.get("msg", body.get("error", exc.reason or "Unknown error")),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CLI helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_LAYOUT_NAMES: dict[int, str] = {
    1: "MindMap (双向导图)",
    2: "RightMap (右向导图)",
    3: "RightTree (右下树状图)",
    4: "DownTree (向下对称树状图)",
    5: "OrgDown (向下组织结构图)",
    6: "OrgTop (向上组织结构图)",
    7: "TimelineRight (向右时间轴)",
    8: "FishboneRight (右向鱼骨图)",
    9: "Sector (扇形放射图)",
    10: "BracketRight (右向括号图)",
    11: "TreeTable (树型表格)",
    12: "Matrix (矩阵图)",
}

_THEME_NAMES: dict[int, str] = {
    1: "Default (通用默认)",
    2: "Knowledge (知识学习)",
    3: "Vivid (活力时尚)",
    4: "Minimal (极简商务)",
    5: "Rainbow (彩虹创意)",
    6: "Paper (纸质文档)",
    7: "Fresh (清爽自然)",
    8: "Dark (暗色默认)",
    9: "Neon (霓虹科技)",
    10: "SciFi (科幻暗黑)",
}

_FILL_NAMES: dict[str, str] = {
    "none": "None (标准平面)",
    "pencil": "Pencil (铅笔素描)",
    "watercolor": "Watercolor (水彩晕染)",
    "charcoal": "Charcoal (木炭素描)",
    "paint": "Paint (油漆涂料)",
    "graffiti": "Graffiti (涂鸦网格)",
}


def _read_input(source: str) -> str:
    """Read Markdown text from a file path or ``-`` for stdin."""
    if source == "-":
        text = sys.stdin.read()
        if not text.strip():
            _die("No input received from stdin.")
        return text

    path = Path(source)
    if not path.is_file():
        _die(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def _info(msg: str) -> None:
    print(f"  {_Color.dim('→')} {msg}", file=sys.stderr)


def _warn(msg: str) -> None:
    print(f"  {_Color.yellow('⚠')} {msg}", file=sys.stderr)


def _die(msg: str, code: int = 1) -> NoReturn:
    print(f"\n  {_Color.red('✗')} {msg}\n", file=sys.stderr)
    raise SystemExit(code)


def _success(msg: str) -> None:
    print(f"  {_Color.green('✓')} {msg}", file=sys.stderr)


def _print_result(result: MindmapResult, *, quiet: bool = False) -> None:
    """Pretty-print the mind map result to stderr, URL to stdout."""
    if quiet:
        print(result.file_url)
        return

    print(file=sys.stderr)
    _success("Mind map generated successfully!")
    print(file=sys.stderr)
    print(
        f"    {_Color.bold('Edit URL')}:      {_Color.cyan(result.file_url)}",
        file=sys.stderr,
    )
    print(
        f"    {_Color.bold('Thumbnail')}:    {result.thumbnail_url}",
        file=sys.stderr,
    )
    ei = result.extra_info
    print(
        f"    {_Color.bold('Request ID')}:   {_Color.dim(ei.request_id)}",
        file=sys.stderr,
    )
    print(
        f"    {_Color.bold('Elapsed')}:      {_Color.dim(str(ei.elapsed_ms) + ' ms')}",
        file=sys.stderr,
    )
    print(file=sys.stderr)

    # Always emit the file_url on stdout so it can be piped.
    print(result.file_url)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Argument parser
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_LAYOUT_HELP = "\n".join(
    f"  {k:>2}  {v}" for k, v in _LAYOUT_NAMES.items()
)

_THEME_HELP = "\n".join(
    f"  {k:>2}  {v}" for k, v in _THEME_NAMES.items()
)

_FILL_HELP = ", ".join(_FILL_NAMES.keys())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edrawmind-cli",
        description=textwrap.dedent("""\
            Convert Markdown to a professional mind map via the EdrawMind API.

            Reads Markdown from a file or stdin (-), sends it to the EdrawMind
            API, and prints the online editing URL.
        """),
        epilog=textwrap.dedent(f"""\
            layout types (--layout):
            {_LAYOUT_HELP}

            theme styles (--theme):
            {_THEME_HELP}

            fill styles (--fill):
              {_FILL_HELP}

            examples:
              %(prog)s notes.md
              %(prog)s --layout 7 --theme 9 timeline.md
              %(prog)s --line-hand-drawn --fill pencil --background 9 sketch.md
              echo "# AI\\n## ML\\n- DL" | %(prog)s -
              %(prog)s --open --json -o result.json input.md
        """),

        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "file",
        metavar="FILE",
        help='Markdown file to convert, or "-" to read from stdin.',
    )

    # ── Styling options ──────────────────────────────────────────────────────
    style = parser.add_argument_group("styling options")

    style.add_argument(
        "-l", "--layout",
        type=int,
        choices=range(1, 13),
        metavar="N",
        dest="layout_type",
        help="Layout type 1–12 (default: 1 — MindMap).",
    )
    style.add_argument(
        "-t", "--theme",
        type=int,
        choices=range(1, 11),
        metavar="N",
        dest="theme_style",
        help="Theme style 1–10.",
    )
    style.add_argument(
        "-b", "--background",
        type=_validate_background,
        metavar="BG",
        help='Background: preset 1–15 or custom "#RRGGBB".',
    )
    style.add_argument(
        "--line-hand-drawn",
        action="store_true",
        default=None,
        help="Use hand-drawn connection lines.",
    )
    style.add_argument(
        "--fill",
        choices=[s.value for s in FillStyle],
        metavar="STYLE",
        dest="fill_hand_drawn",
        help=f"Node fill style: {_FILL_HELP}.",
    )

    # ── Connection options ───────────────────────────────────────────────────
    conn = parser.add_argument_group("connection options")

    conn.add_argument(
        "--api-key",
        metavar="KEY",
        help="API key for authentication.",
    )
    conn.add_argument(
        "--api-url",
        metavar="URL",
        help="API endpoint URL (default: built-in).",
    )

    # ── Output options ───────────────────────────────────────────────────────
    out = parser.add_argument_group("output options")

    out.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Save the JSON response to a file.",
    )
    out.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print full JSON response to stdout.",
    )
    out.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only print the file URL to stdout (no decoration).",
    )
    out.add_argument(
        "--open",
        action="store_true",
        dest="open_browser",
        help="Open the mind map URL in the default browser.",
    )
    out.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip Markdown input validation.",
    )
    out.add_argument(
        "--insecure",
        action="store_true",
        help="Skip SSL certificate verification (for dev/self-signed certs).",
    )
    out.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def _validate_background(value: str) -> str:
    """Argparse type validator for the --background option."""
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value
    if value.isdigit() and 1 <= int(value) <= 15:
        return value
    raise argparse.ArgumentTypeError(
        f"Invalid background '{value}'. Use a preset 1–15 or #RRGGBB."
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Main entry point
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns an exit code (0 = success)."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # ── Resolve API configuration ────────────────────────────────────────────
    api_key: str | None = args.api_key
    api_url: str = args.api_url or _DEFAULT_API_URL

    # ── Read input ───────────────────────────────────────────────────────────
    text = _read_input(args.file)

    # ── Validate ─────────────────────────────────────────────────────────────
    if not args.no_validate:
        warnings = validate_markdown(text)
        for w in warnings:
            _warn(w)
        if any("heading" in w.lower() or "empty" in w.lower() for w in warnings):
            _die(
                "Input does not look like valid Markdown for mind map generation. "
                "Use --no-validate to bypass."
            )

    # ── Resolve --line-hand-drawn sentinel ───────────────────────────────────
    line_hand_drawn: bool | None = True if args.line_hand_drawn else None

    # ── Call API ─────────────────────────────────────────────────────────────
    _info(f"Sending {len(text):,} characters to {api_url} …")

    try:
        result = markdown_to_mindmap(
            text,
            api_url=api_url,
            api_key=api_key,
            layout_type=args.layout_type,
            theme_style=args.theme_style,
            background=args.background,
            line_hand_drawn=line_hand_drawn,
            fill_hand_drawn=args.fill_hand_drawn,
            insecure=args.insecure,
        )
    except RateLimitError as exc:
        retry = f" Retry after {exc.retry_after}s." if exc.retry_after else ""
        _die(f"Rate limited ({exc.code}).{retry}")
    except APIError as exc:
        _die(f"API error: {exc}")
    except EdrawMindError as exc:
        _die(str(exc))

    # ── Output ───────────────────────────────────────────────────────────────
    response_dict = asdict(result)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(
            json.dumps(response_dict, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        _info(f"Response saved to {out_path}")

    if args.json_output:
        print(json.dumps(response_dict, indent=2, ensure_ascii=False))
    else:
        _print_result(result, quiet=args.quiet)

    if args.open_browser:
        _info("Opening in browser …")
        webbrowser.open(result.file_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
