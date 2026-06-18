#!/usr/bin/env python3
"""
build_web_skills.py — generate the web edition of the Agentic AI PM Skill Package.

Source: ../../skills/agentic-pm-skill-package/<skill>/SKILL.md
Output: series-web/skills/<skill>.html  (one page per skill)
        series-web/skills/index.html    (landing page; rebuilt by this script)

Reuses the markdown-to-HTML engine from build_web_book5.py and the styling
from book3/styles.css. Each skill page has a left sidebar listing all seven
skills with the active one highlighted, and a main content area rendering
the SKILL.md body. YAML frontmatter is parsed and surfaced as eyebrow + sub-headline.

Run from the series-web/ directory:
    python3 build_web_skills.py
"""
from __future__ import annotations
import re, html, shutil
from pathlib import Path

HERE        = Path(__file__).resolve().parent
SKILLS_SRC  = HERE.parent.parent / "skills" / "agentic-pm-skill-package"
OUT         = HERE / "skills"
OUT.mkdir(exist_ok=True)

SITE_TITLE = "Agentic AI PM Skill Package"
SITE_SUB   = "The lifecycle, as working aids a PM can invoke at the moment of need"
CANON      = "https://agenticaiproductmanagement.com/skills/"
HUB        = "../index.html"
RELEASES   = "https://github.com/yoramfmd/agentic-ai-pm-skill-package/releases/latest"
REPO_URL   = "https://github.com/yoramfmd/agentic-ai-pm-skill-package"

# Skill order (matches the landing page row order). Each tuple: (slug, eyebrow, color).
SKILLS = [
    ("agentic-pm-lifecycle",            "Router",                              "#6B7280"),
    ("agentic-pm-discover-decide",      "Phase 1 · Discover & Decide",         "#378ADD"),
    ("agentic-pm-design",               "Phase 2 · Design",                    "#7c3aed"),
    ("agentic-pm-eval",                 "Phase 3 · Eval",                      "#1D9E75"),
    ("agentic-pm-observe",              "Phase 4 · Observe",                   "#D97706"),
    ("agentic-pm-operate",              "Phase 5 · Operate",                   "#C2410C"),
    ("agentic-pm-behavior-governance",  "Cross-phase · Strategic posture",     "#BE185D"),
]


def parse_frontmatter(md: str):
    """Pull YAML frontmatter and return (frontmatter_dict, body_md)."""
    m = re.match(r"^---\n(.*?)\n---\n", md, re.DOTALL)
    if not m:
        return {}, md
    block = m.group(1)
    body = md[m.end():]
    fm = {}
    # Simple parser: keys at column 0, values on same line or continuation lines.
    current_key = None
    for line in block.splitlines():
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_-]*:", line):
            key, _, rest = line.partition(":")
            key = key.strip()
            val = rest.strip()
            if val == ">" or val == "|":
                fm[key] = ""
                current_key = key
            else:
                fm[key] = val
                current_key = None
        elif current_key is not None and (line.startswith("  ") or line.startswith("\t")):
            fm[current_key] += (" " if fm[current_key] else "") + line.strip()
    return fm, body


def slug(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:60] or "section"


# ── inline markdown → HTML ────────────────────────────────────────────────────

def inline(s: str) -> str:
    # Inline code (backticks) — protect first so we don't process markdown inside
    placeholders = []
    def stash_code(m):
        placeholders.append(html.escape(m.group(1), quote=False))
        return f"\0CODE{len(placeholders)-1}\0"
    s = re.sub(r"`([^`]+)`", stash_code, s)

    # Bold, italic, links
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)

    # Escape text nodes (everything not inside tags)
    def escape_text_nodes(t):
        return re.sub(r"(?<=>)([^<]+)(?=<)|^([^<]+)(?=<)|(?<=>)([^<]+)$|^([^<]+)$",
                      lambda m: html.escape(m.group(0), quote=False), t)
    s = escape_text_nodes(s)

    # Restore inline code
    for i, c in enumerate(placeholders):
        s = s.replace(f"\0CODE{i}\0", f"<code>{c}</code>")

    # Smart quotes
    out_chars = []; opn = True
    for ch in s:
        if ch == '"':
            out_chars.append("&ldquo;" if opn else "&rdquo;"); opn = not opn
        else:
            out_chars.append(ch)
    s = "".join(out_chars)
    s = re.sub(r"(\w)'(\w)", r"\1&rsquo;\2", s)
    s = re.sub(r"(?<=\w)'", "&rsquo;", s)
    s = s.replace("'", "&lsquo;")
    return s


# ── block parser ──────────────────────────────────────────────────────────────

def render_body(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0; n = len(lines)

    def parse_table(tbl_lines):
        rows = [r for r in tbl_lines if r.strip().startswith("|")]
        if len(rows) < 2: return ""
        def cells(r): return [c.strip() for c in r.strip().strip("|").split("|")]
        head = cells(rows[0]); body = [cells(r) for r in rows[2:]]
        h = ["    <table>", "      <thead>", "        <tr>"]
        for c in head: h.append(f"          <th>{inline(c)}</th>")
        h += ["        </tr>", "      </thead>", "      <tbody>"]
        for br in body:
            h.append("        <tr>")
            for c in br: h.append(f"          <td>{inline(c)}</td>")
            h.append("        </tr>")
        h += ["      </tbody>", "    </table>"]
        return "\n".join(h)

    while i < n:
        raw = lines[i]; s = raw.strip()

        # Code fence
        if s.startswith("```"):
            i += 1
            code_lines = []
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i]); i += 1
            i += 1  # skip closing fence
            code = "\n".join(code_lines)
            out.append(f"    <pre><code>{html.escape(code, quote=False)}</code></pre>")
            continue

        if s.startswith("<!--"): i += 1; continue
        if not s: i += 1; continue

        # H1 in body — only shows up if the source has it (we strip the first H1 in the caller)
        if s.startswith("# ") and not s.startswith("## "):
            t = s[2:]
            out.append(f'    <h1 id="{slug(t)}">{inline(t)}</h1>'); i += 1; continue

        # H2
        if s.startswith("## "):
            t = s[3:]
            out.append(f'    <h2 id="{slug(t)}">{inline(t)}</h2>'); i += 1; continue
        # H3
        if s.startswith("### "):
            t = s[4:]
            out.append(f'    <h3 id="{slug(t)}">{inline(t)}</h3>'); i += 1; continue
        # H4
        if s.startswith("#### "):
            t = s[5:]
            out.append(f'    <h4 id="{slug(t)}">{inline(t)}</h4>'); i += 1; continue

        # HR
        if re.match(r"^-{3,}$", s):
            out.append("    <hr>"); i += 1; continue

        # Table
        if s.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i]); i += 1
            out.append(parse_table(tbl)); continue

        # Blockquote
        if s.startswith(">"):
            block = []
            while i < n and (lines[i].strip().startswith(">") or
                             (block and not lines[i].strip())):
                block.append(lines[i]); i += 1
            inner_lines = [re.sub(r"^>\s?", "", bl) for bl in block if bl.strip()]
            inner_md = "\n".join(inner_lines)
            first = inner_lines[0] if inner_lines else ""
            if re.match(r"^\*\*.+\*\*", first.strip()):
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", first.strip(), count=1)
                rest_md = "\n".join(inner_lines[1:])
                out.append(f'    <div class="callout">')
                out.append(f'      <div class="callout-title">{inline(title)}</div>')
                out.append("      " + render_body(rest_md).strip())
                out.append("    </div>")
            else:
                bq_inner = "\n".join(f"<p>{inline(l)}</p>" for l in inner_lines if l.strip())
                out.append(f"    <blockquote>{bq_inner}</blockquote>")
            continue

        # Unordered list
        if re.match(r"^[-*+]\s", s):
            items = []
            while i < n and re.match(r"^[-*+]\s", lines[i].strip()):
                items.append(lines[i].strip()[2:]); i += 1
            out.append("    <ul>")
            for it in items:
                out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ul>")
            continue

        # Ordered list
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[i].strip())); i += 1
            out.append("    <ol>")
            for it in items:
                out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ol>")
            continue

        # Paragraph
        para_lines = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", ">", "|", "```")) \
              and not re.match(r"^-{3,}$", lines[i].strip()) \
              and not re.match(r"^[-*+]\s", lines[i].strip()) \
              and not re.match(r"^\d+\.\s", lines[i].strip()):
            para_lines.append(lines[i].strip()); i += 1
        text = " ".join(para_lines)
        if text:
            out.append(f"    <p>{inline(text)}</p>")

    return "\n".join(out)


# ── sidebar ───────────────────────────────────────────────────────────────────

def build_sidebar(active_slug: str) -> str:
    items = []
    items.append(f'    <div class="sidebar-hub"><a href="{HUB}">&larr; The Agentic AI Series</a></div>')
    items.append(f'    <div class="sidebar-brand"><a href="index.html">{SITE_TITLE}</a>'
                 f'<div class="sidebar-brand-sub">{SITE_SUB}</div></div>')
    items.append('    <ul class="sidebar-list">')
    for slug_, eyebrow, color in SKILLS:
        active_cls = ' class="active"' if slug_ == active_slug else ""
        items.append(f'      <li><a href="{slug_}.html"{active_cls}>')
        items.append(f'        <div class="sidebar-eyebrow" style="color:{color}">{eyebrow}</div>')
        items.append(f'        <div class="sidebar-skill-name">{slug_}</div>')
        items.append('      </a></li>')
    items.append("    </ul>")
    items.append(f'    <div class="sidebar-cta"><a href="{RELEASES}" target="_blank" rel="noopener">Install all seven &rarr;</a></div>')
    return "\n".join(items)


# ── page shell ────────────────────────────────────────────────────────────────

def page_shell(skill_slug: str, eyebrow: str, color: str, title: str, description: str, body_html: str) -> str:
    sidebar = build_sidebar(skill_slug)
    install_url = f"{REPO_URL}/raw/main/releases/{skill_slug}.skill"
    desc_meta = html.escape(description[:160])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} &mdash; {SITE_TITLE}</title>
<meta name="description" content="{desc_meta}">
<link rel="canonical" href="{CANON}{skill_slug}.html">
<link rel="stylesheet" href="../book3/styles.css">
<style>
  .sidebar-hub {{ margin-bottom: var(--space-4); padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--rule); font-size: 12px; font-family: var(--sans); }}
  .sidebar-hub a {{ color: var(--ink-muted); text-decoration: none; }}
  .sidebar-hub a:hover {{ color: var(--blue-deep); }}
  .sidebar-list li a {{ padding: var(--space-3) var(--space-3); }}
  .sidebar-list li a.active {{ background: var(--tint-warm); border-radius: var(--radius-md); }}
  .sidebar-eyebrow {{ font-family: var(--sans); font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 3px; }}
  .sidebar-skill-name {{ font-family: var(--mono, monospace); font-size: 12px; color: var(--ink); font-weight: 500; }}
  .sidebar-cta {{ margin-top: var(--space-5); padding-top: var(--space-4); border-top: 1px solid var(--rule); font-family: var(--sans); font-size: 13px; }}
  .sidebar-cta a {{ color: var(--blue-deep); text-decoration: none; }}
  .sidebar-cta a:hover {{ text-decoration: underline; }}

  .chapter pre {{ background: var(--tint-warm); border-radius: var(--radius-md); padding: var(--space-4); overflow-x: auto; font-family: var(--mono, monospace); font-size: 12.5px; line-height: 1.55; color: var(--ink); margin: var(--space-4) 0; }}
  .chapter code {{ background: var(--tint-warm); padding: 1px 6px; border-radius: 4px; font-family: var(--mono, monospace); font-size: 0.9em; }}
  .chapter pre code {{ background: transparent; padding: 0; }}

  .skill-header {{ margin-bottom: var(--space-6); padding-bottom: var(--space-5); border-bottom: 1px solid var(--rule); }}
  .skill-eyebrow {{ font-family: var(--sans); font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: {color}; margin-bottom: var(--space-2); }}
  .skill-slug {{ font-family: var(--mono, monospace); font-size: 14px; color: var(--ink-muted); margin-bottom: var(--space-2); }}
  .skill-title {{ font-family: var(--serif); font-size: 34px; font-weight: 700; line-height: 1.15; color: var(--ink); margin-bottom: var(--space-3); }}
  .skill-description {{ font-family: var(--sans); font-size: 14px; line-height: 1.65; color: var(--ink-soft); margin-bottom: var(--space-4); padding: var(--space-4); background: var(--tint-warm); border-left: 3px solid {color}; border-radius: var(--radius-md); }}
  .skill-install-row {{ display: flex; gap: var(--space-3); flex-wrap: wrap; margin-top: var(--space-4); }}
  .install-btn {{ padding: var(--space-2) var(--space-4); font-family: var(--sans); font-size: 13px; font-weight: 500; border-radius: var(--radius-md); text-decoration: none; border: 1px solid var(--ink); }}
  .install-primary {{ background: var(--ink); color: var(--bg); }}
  .install-secondary {{ background: transparent; color: var(--ink); }}
  .install-primary:hover {{ background: var(--ink-soft); }}
  .install-secondary:hover {{ background: var(--tint-warm); }}
</style>
</head>
<body>
<div class="book">
  <aside class="sidebar">
{sidebar}
  </aside>
  <div class="main">
    <div class="chapter">
      <div class="skill-header">
        <div class="skill-eyebrow">{eyebrow}</div>
        <div class="skill-slug">{skill_slug}</div>
        <h1 class="skill-title">{html.escape(title)}</h1>
        <div class="skill-description">{inline(description)}</div>
        <div class="skill-install-row">
          <a class="install-btn install-primary" href="{install_url}" download>Install this skill</a>
          <a class="install-btn install-secondary" href="{RELEASES}" target="_blank" rel="noopener">Install all seven</a>
        </div>
      </div>
{body_html}
    </div>
  </div>
</div>
</body>
</html>"""


# ── extract title from SKILL.md ───────────────────────────────────────────────

def extract_title(body: str) -> str:
    m = re.search(r"^# (.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else ""


def generate():
    if not SKILLS_SRC.exists():
        print(f"ERROR: skills source not found at {SKILLS_SRC}")
        return

    print(f"Reading from: {SKILLS_SRC}")
    print(f"Writing to:   {OUT}")
    print()

    for skill_slug, eyebrow, color in SKILLS:
        src = SKILLS_SRC / skill_slug / "SKILL.md"
        if not src.exists():
            print(f"  MISSING: {src}")
            continue

        md = src.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(md)

        title = extract_title(body)
        if not title:
            title = skill_slug

        # Strip the first H1 (we render it from extracted title)
        body = re.sub(r"^# .+\n", "", body, count=1)

        description = fm.get("description", "").strip()
        # Clean up the description: strip leading colon if YAML > was misparsed
        if description.startswith(": "):
            description = description[2:]

        body_html = render_body(body)

        page = page_shell(skill_slug, eyebrow, color, title, description, body_html)
        out_path = OUT / f"{skill_slug}.html"
        out_path.write_text(page, encoding="utf-8")
        print(f"  {skill_slug}.html")

    # Update the install button on index.html to also link to per-skill pages
    # (We leave the existing landing page in place; it already exists.)
    print()
    print("Done. Output: skills/")


if __name__ == "__main__":
    generate()
