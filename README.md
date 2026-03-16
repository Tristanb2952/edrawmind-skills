# EdrawMind Mindmap AI Skill

> **Author:** EdrawMind AI Team · **Organization:** Wondershare EdrawMind  
> **Version:** 1.0.0 · **License:** Proprietary © 2026 Wondershare EdrawMind. All rights reserved.

An AI skill for AI Agents (OpenClaw, GitHub Copilot, Claude Code, etc.) that generates professional mind maps from Markdown content using the MCP tool `markdown_to_mindmap`.

---

## What This Skill Does

The `edrawmind-mindmap` skill converts structured Markdown content into professional mind maps. After generation, it returns an online editing link and a thumbnail preview. The mind map can be edited in the **EdrawMind** web editor, or exported as `.emmx` for desktop use.

### Use Cases

- Outlines and summaries
- Meeting notes
- Study notes and knowledge organization
- Project planning and task breakdown
- Reading notes and knowledge frameworks
- Code architecture visualization

### What Problems It Solves

- **No design skills needed** — just prepare structured Markdown text; the AI handles layout and rendering automatically.
- **Instant online preview** — get an online editing link and thumbnail right after generation.
- **Exportable and editable** — mind maps can be exported as `.emmx` for further editing in the EdrawMind desktop app.

---

## Installation

Add the `skills/edrawmind-mindmap` directory from this repository to your AI Agent's skill directory.

---

## Quick Start

### Trigger Phrases

The skill activates automatically when you say things like:

- *"Create a mind map for machine learning concepts"*
- *"Convert this Markdown document into a mind map"*
- *"Generate a mind map of the project architecture"*

### MCP Tool Call

**Tool name:** `markdown_to_mindmap`

**Parameters:**

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | Yes | Valid Markdown text. Must contain at least one level-1 or level-2 heading (`#` or `##`) and at least one list item (`-`, `*`, `+`, or `1.`). Plain prose text is not accepted. |

### Markdown Input Requirements

- Must contain at least one heading (`#` or `##`)
- Must contain at least one list item (`-`, `*`, `+`, or `1.`)
- Use `#` for the root/central topic, `##` for first-level branches, `###` for second-level branches
- Use `-` list items for child nodes; indented list items for deeper nodes
- Keep node text concise (3-5 words recommended)
- Recommended max depth: 4-5 levels, max ~80 nodes

**Input example:**

```markdown
# Project Architecture
## Frontend
- React
- TypeScript
## Backend
- Python
- FastAPI
## Database
- PostgreSQL
- Redis
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

| Field | Type | Description |
|---|---|---|
| `file_url` | string | Online editing link for the mind map. **Must be shown to the user.** |
| `thumbnail_url` | string | Thumbnail preview URL |
| `extra_info.elapsed_ms` | number | Server-side generation time (ms) |
| `extra_info.request_id` | string | Unique request identifier |

The tool also returns an image content block containing a thumbnail preview of the mind map, which can be displayed directly in chat interfaces.

---

## Important Notes

- Content must be structured: plain text paragraphs cannot generate mind maps correctly; use headings and lists
- The `#` heading becomes the central topic; use only one level-1 heading per mind map
- Keep depth to 4-5 levels for best readability
- For large documents (100+ headings), consider splitting into multiple mind maps by top-level sections
- **Always show the returned `file_url` to the user** so they can access and edit the mind map
- Display the returned thumbnail when image rendering is supported

---

## Copyright

© 2026 Wondershare EdrawMind AI Team. All rights reserved.

This skill and all associated resources are proprietary to Wondershare EdrawMind. Unauthorized copying, modification, distribution, or reverse engineering is strictly prohibited.

See [`skills/edrawmind-mindmap/license.txt`](skills/edrawmind-mindmap/license.txt) for full license terms.

---

## FAQ

**Q: Is the EdrawMind mindmap skill free to use?**  
A: Yes — it is currently free of charge during the promotional period.

**Q: What output formats are available?**  
A: Generation returns an online editing link and a thumbnail preview. You can edit in the EdrawMind web editor or export as `.emmx` for desktop use.

**Q: Is my data safe?**  
A: Markdown content is transmitted over HTTPS. Do not include sensitive or personally identifiable information in your content.

**Q: How do I report a bug or request a feature?**  
A: Send an email to 📧 **ws-business@wondershare.cn** describing the issue or feature request.
