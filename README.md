# EdrawMind Mindmap AI Skill

> **Author:** EdrawMind AI Team · **Organization:** Wondershare EdrawMind
> **Version:** 1.0.0 · **License:** Proprietary © 2026 Wondershare EdrawMind. All rights reserved.

[中文版](README_CN.md)

An AI skill for AI Agents (GitHub Copilot, Claude Code, etc.) that generates professional mind maps from Markdown content. Supports customizable layouts, themes, backgrounds, and hand-drawn styles.

---

## What This Skill Does

The `edrawmind-mindmap` skill converts structured Markdown into professional mind maps via the EdrawMind HTTP API. It supports 12 layout types, 10 theme styles, 15 background presets, and multiple hand-drawn effects.

### Use Cases

- Outlines and summaries
- Meeting notes and study notes
- Project planning and task breakdown
- Code architecture visualization
- Knowledge frameworks and reading notes

### What Problems It Solves

- **No design skills needed** — prepare Markdown text; the AI handles layout and rendering automatically.
- **Rich customization** — choose from 12 layouts (mind map, timeline, fishbone, org chart, etc.), 10 themes, and hand-drawn styles.
- **Instant online preview** — get an online editing link and thumbnail right after generation.

---

## Project Structure

```
edrawmind-skills/
├── build.bat                       # Build entry — Windows
├── build.sh                        # Build entry — Linux / macOS
├── pyproject.toml                  # Project config (uv / pip)
├── scripts/
│   └── build.py                    # Build script — packages skill into zip
├── skills/
│   └── edrawmind-mindmap/          # The skill directory
│       ├── SKILL.md                # Skill definition (agent reads this)
│       ├── license.txt
│       ├── docs/                   # Internal dev docs (excluded from zip)
│       ├── references/             # Reference docs (loaded on demand)
│       │   ├── markdown-format.md
│       │   ├── style-guide.md
│       │   └── tool-reference.md
│       └── scripts/
│           └── edrawmind_cli.py    # CLI tool for HTTP API
├── README.md
└── README_CN.md
```

---

## Installation

### From Release Zip

1. Download `edrawmind-mindmap.zip` from [Releases](../../releases)
2. Unzip into your AI Agent's skill directory:
   - **GitHub Copilot**: `.github/skills/`
   - **Claude Code**: `.claude/skills/`
   - **General**: `.agents/skills/`

### From Source

```bash
git clone <repo-url>
cd edrawmind-skills
```

---

## Build

Package the skill into a distributable zip (excludes `docs/`):

```bash
# Windows
build.bat

# Linux / macOS
./build.sh

# Or via Python / uv directly
python scripts/build.py
uv run python scripts/build.py

# Custom output path
build.bat -o dist/custom-name.zip

# Dry run — list files only
build.bat --list
```

Output: `dist/edrawmind-mindmap.zip`

---

## Quick Start

### Trigger Phrases

The skill activates automatically when you say things like:

- *"Create a mind map for machine learning concepts"*
- *"Convert this Markdown into a mind map"*
- *"Generate a mind map of the project architecture"*

### CLI Tool

The skill uses `edrawmind_cli.py` to call the EdrawMind HTTP API:

```bash
# Basic
python edrawmind_cli.py input.md

# With layout, theme, and background
python edrawmind_cli.py --layout 7 --theme 9 --background 4 timeline.md

# Hand-drawn style
python edrawmind_cli.py --line-hand-drawn --fill pencil --background 9 notes.md
```

### Response

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

| Field | Description |
|---|---|
| `file_url` | Online editing link. **Must be shown to the user.** |
| `thumbnail_url` | Thumbnail preview URL |

---

## Styling Options

| Parameter | Range | Description |
|-----------|-------|-------------|
| `--layout N` | 1–12 | Layout type (mind map, timeline, fishbone, org chart, etc.) |
| `--theme N` | 1–10 | Theme style (default, knowledge, vivid, minimal, etc.) |
| `--background BG` | 1–15 or `#RRGGBB` | Canvas background |
| `--line-hand-drawn` | flag | Hand-drawn connection lines |
| `--fill STYLE` | none/pencil/watercolor/charcoal/paint/graffiti | Node fill style |

See [style-guide.md](skills/edrawmind-mindmap/references/style-guide.md) for detailed parameter descriptions.

---

## Important Notes

- Content must be structured Markdown with headings and lists
- Use only one `#` heading as the root node
- Recommended: max 5 levels deep, ~80 nodes
- For large documents (100+ headings), split by chapter
- **Always show the returned `file_url` to the user**

---

## Copyright

© 2026 Wondershare EdrawMind AI Team. All rights reserved.

See [`skills/edrawmind-mindmap/license.txt`](skills/edrawmind-mindmap/license.txt) for full license terms.

---

## FAQ

**Q: Is the EdrawMind mindmap skill free to use?**
A: Yes — it is currently free during the promotional period.

**Q: What output formats are available?**
A: Returns an online editing link and thumbnail. Export as `.emmx` for desktop editing in EdrawMind.

**Q: Is my data safe?**
A: Markdown content is transmitted over HTTPS. Do not include sensitive information.

**Q: How do I report a bug?**
A: Email 📧 **ws-business@wondershare.cn**
