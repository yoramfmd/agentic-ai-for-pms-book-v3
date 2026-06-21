#!/usr/bin/env python3
"""
build_web_book5.py — generate the web edition of The Agentic Team.

Source: Books/AgenticTeam/chapters/**/*.md  (per-chapter authoritative files)
Output: series-web/book5/                   (flat HTML, GitHub Pages ready)

Run from the series-web/ directory:
    python3 build_web_book5.py
"""
from __future__ import annotations
import re, html, shutil
from pathlib import Path

HERE     = Path(__file__).resolve().parent
CHAPTERS = HERE.parent / "AgenticTeam" / "chapters"
OUT      = HERE / "book5"
OUT.mkdir(exist_ok=True)

SITE_TITLE = "The Agentic AI Team"
SITE_SUB   = "How Agentic AI Reshapes the Roles That Build It"
CANON      = "https://agenticaiproductmanagement.com/book5/"
HUB        = "../index.html"
DRAFT      = False  # adds "Draft" to landing eyebrow and sidebar brand title

# (md-path-relative-to-chapters/, sidebar-label, section, display-num)
# section: "front" | "part" | "ref"
# display-num: int for chapters, roman str for parts, None for front/ref
PAGES = [
    # ── Part I: Foundations ──
    ("sec-foundations/01-what-youre-building.md",              "What You Are Actually Building",           "part1", 1),
    ("sec-foundations/02-deciding-what-to-build.md",           "Deciding What to Build, and Whether To",   "part1", 2),
    ("sec-foundations/03-the-triad-premise.md",                "The Team Was Built for a Different Product","part1", 3),
    # ── Part II: The Work Reshapes ──
    ("sec-work-reshapes/00-OPENER.md",                         "The Work Reshapes",                        "part2", None),
    ("sec-work-reshapes/01-ux-DRAFT.md",                       "Is There Still a UX?",                     "part2", 4),
    ("sec-work-reshapes/02-dev-DRAFT.md",                      "Who Wrote This Code, and Who Answers for It?","part2", 5),
    ("sec-work-reshapes/03-scrum-DRAFT.md",                    "Is There Still a Scrum?",                  "part2", 6),
    ("sec-work-reshapes/04-architect-DRAFT.md",                "Whose Job Is It That the Whole Thing Holds?","part2", 7),
    ("sec-work-reshapes/05-pm-DRAFT.md",                       "What’s Left for the PM?",             "part2", 8),
    # ── Part III: Failures (Re-vantage) ──
    ("sec-revantage/01-silent-degradation.md",                 "The Failure No One Is Watching",           "part3", 9),
    ("sec-revantage/01b-the-calendar-the-agent-could-not-see.md","The Calendar the Agent Could Not See",   "part3", 10),
    ("sec-revantage/02-the-boundary-and-the-wall.md",          "The Boundary and the Wall",                "part3", 11),
    ("sec-revantage/03-the-green-checkmark.md",                "The Green Checkmark Nobody Owned",         "part3", 12),
    ("sec-revantage/04-who-watches-who-stops.md",              "Who Watches It, and Who Can Stop It",      "part3", 13),
    ("sec-revantage/05-built-before-enforced-at-the-moment.md","Built Before, Authorized at the Moment",   "part3", 14),
    ("sec-revantage/06-the-people-the-agent-erodes.md",        "The People the Agent Is Eroding",          "part3", 15),
    # ── Part IV: The Collaboration Model ──
    ("sec-collaboration/00-the-grid.md",                       "The Model Is Old. The Column Is New.",     "part4", 16),
    ("sec-collaboration/01-filling-the-grid.md",               "Filling the Grid",                         "part4", 17),
    ("sec-collaboration/02-what-flows-between-the-cells.md",   "What Flows Between the Cells",             "part4", 18),
    # ── Part V: The Org Model ──
    ("sec-org-model/00-grow-the-box.md",                       "Start With the Box You Already Have",      "part5", 19),
    ("sec-org-model/01-the-team-member-nobody-hired.md",       "The Team Member Nobody Hired",             "part5", 20),
    ("sec-org-model/02-staffing-by-stage.md",                  "Who Sits in the New Seats",                "part5", 21),
    # ── Part VI: Agents Building Agents ──
    ("sec-agents-building-agents/00-the-team-member-who-hires.md","The Team Member Who Hires",             "part6", 22),
    ("sec-agents-building-agents/01-who-watches-the-watchers.md","When the Watchers Are Agents Too",       "part6", 23),
    ("sec-agents-building-agents/02-governing-the-fleet.md",   "Governing What You Cannot Watch",          "part6", 24),
    # ── Part VII: Carry the Weight ──
    ("sec-carry-the-weight/00-the-constitution.md",            "The Agent’s Constitution",            "part7", 25),
    ("sec-carry-the-weight/01-carry-the-weight.md",            "Carry the Weight",                         "part7", 26),
    # ── Back matter ──
    ("sec-back-matter/zz-references.md",                       "References and Sources",                   "ref",   None),
]

PART_LABELS = {
    "part1": "Part I · Foundations",
    "part2": "Part II · The Work Reshapes",
    "part3": "Part III · Failures",
    "part4": "Part IV · The Collaboration Model",
    "part5": "Part V · The Org Model",
    "part6": "Part VI · Agents Building Agents",
    "part7": "Part VII · Carry the Weight",
    "ref":   "Reference",
}

def out_name(md_path: str) -> str:
    stem = Path(md_path).stem
    # strip -DRAFT suffix
    stem = re.sub(r"-DRAFT$", "", stem, flags=re.IGNORECASE)
    # strip leading sort prefixes like 00-, 01b-
    stem = re.sub(r"^(\d+[a-z]?)-", "", stem)
    # strip zz- prefix
    stem = re.sub(r"^zz-", "", stem)
    return stem + ".html"

def slug(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:60] or "section"

# ── inline markdown → HTML ────────────────────────────────────────────────────

def inline(s: str) -> str:
    # Apply markdown substitutions BEFORE escaping so output tags aren't clobbered
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    def escape_text_nodes(t):
        return re.sub(r"(?<=>)([^<]+)(?=<)|^([^<]+)(?=<)|(?<=>)([^<]+)$|^([^<]+)$",
                      lambda m: html.escape(m.group(0), quote=False), t)
    s = escape_text_nodes(s)
    # smart double quotes
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
    # Strip YAML front-matter
    md = re.sub(r"^---\n.*?\n---\n", "", md, flags=re.DOTALL)

    # Strip the leading italic editorial preamble.
    # The H1 has already been removed by the caller (body_md = re.sub(r"^# .+\n", "", md)).
    # Pattern: optional blanks, then one italic block (*...*), optional blanks, optional --- separator.
    md = re.sub(
        r"(?ms)\A\s*\*(?!\s).*?(?<!\s)\*\s*\n(?:\s*-{3,}\s*\n)?",
        "",
        md,
    )

    # Truncate body at trailing build-time sections that must not ship.
    # Cuts everything from the first such heading to the end of the file.
    md = re.sub(
        r"(?ms)\n+(?:-{3,}\s*\n+)?##\s+(?:Notes and sources|Draft notes\b[^\n]*)\b.*\Z",
        "\n",
        md,
    )

    # Strip build/editorial notes in italics on first lines after H1
    lines = md.split("\n")
    out: list[str] = []
    i = 0; n = len(lines)
    pocket_html: str | None = None

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

    # Skip H1 (handled by shell) and build-note italics immediately after H1
    skip_build_note = False
    while i < n:
        raw = lines[i]; s = raw.strip()

        if s.startswith("<!--"): i += 1; continue
        if not s: i += 1; continue

        # H1 — skip; the shell renders it
        if s.startswith("# ") and not s.startswith("## ") and not s.startswith("### "):
            skip_build_note = True; i += 1; continue

        # Build/editorial note line right after H1 (italicized metadata)
        if skip_build_note and re.match(r"^\*.+\*$", s) and not re.match(r"^\*Stage:", s):
            # Check if it looks like a build note (contains "ch", "merged", "canon", "voice")
            if re.search(r"\b(merged|canon|ch\d|voice|Source:|DRAFT|REVANTAGE)", s):
                i += 1; continue
        skip_build_note = False

        # Stage line
        if re.match(r"^\*(Stage:[^*]+|Field reference)\*$", s): i += 1; continue

        # H2
        if s.startswith("## "):
            t = s[3:]
            out.append(f'    <h2 id="{slug(t)}">{inline(t)}</h2>'); i += 1; continue
        # H3
        if s.startswith("### "):
            t = s[4:]
            out.append(f'    <h3 id="{slug(t)}">{inline(t)}</h3>'); i += 1; continue

        # HR
        if re.match(r"^-{3,}$", s):
            out.append("    <hr>"); i += 1; continue

        # Table
        if s.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i]); i += 1
            out.append(parse_table(tbl)); continue

        # Blockquote / callout
        if s.startswith(">"):
            block = []
            while i < n and (lines[i].strip().startswith(">") or
                             (block and not lines[i].strip())):
                block.append(lines[i]); i += 1
            inner_lines = [re.sub(r"^>\s?", "", bl) for bl in block if bl.strip()]
            inner_md = "\n".join(inner_lines)
            # "Keep in your pocket" box
            if re.search(r"keep in your pocket", inner_md, re.IGNORECASE):
                pocket_out = ['    <div class="callout callout-pocket">',
                              '      <div class="callout-label">Keep in your pocket</div>']
                pocket_out.append("      " + render_body(
                    re.sub(r"\*\*keep in your pocket\*\*\n?", "", inner_md, flags=re.IGNORECASE).strip()
                ).strip())
                pocket_out.append("    </div>")
                pocket_html = "\n".join(pocket_out)
            else:
                # Generic callout if it has bold first line, else blockquote
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
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", ">", "|", "-"*3)) \
              and not re.match(r"^[-*+]\s", lines[i].strip()) \
              and not re.match(r"^\d+\.\s", lines[i].strip()):
            para_lines.append(lines[i].strip()); i += 1
        text = " ".join(para_lines)
        if text:
            out.append(f"    <p>{inline(text)}</p>")

    result = "\n".join(out)
    if pocket_html:
        result += "\n" + pocket_html
    return result

# ── sidebar builder ───────────────────────────────────────────────────────────

def _is_part_opener_book5(section, num):
    """A part-opener is a partN entry with no chapter number."""
    return section.startswith("part") and num is None


def build_sidebar(active_md: str) -> str:
    items: list[str] = []

    # Hub link at top
    items.append(f'    <div class="sidebar-hub"><a href="{HUB}">&larr; All Books</a></div>')
    draft_tag = ' <span style="font-size:11px;font-weight:400;color:var(--ink-muted)">(Draft)</span>' if DRAFT else ''
    items.append(f'    <div class="sidebar-brand"><a href="index.html">{SITE_TITLE}{draft_tag}</a>'
                 f'<div class="sidebar-brand-sub">{SITE_SUB}</div></div>')

    # Map each section to its part-opener entry, so we can link the section header to it.
    section_opener = {}
    for (md_path, label, section, num) in PAGES:
        if _is_part_opener_book5(section, num):
            section_opener[section] = (md_path, label)

    current_part = None
    for (md_path, label, section, num) in PAGES:
        part = section if section.startswith("part") else "ref"
        # New section header
        if part != current_part:
            # Close the previous <ul> before opening a new section
            if current_part is not None:
                items.append("    </ul>")
            current_part = part
            if part == "ref":
                items.append('    <div class="sidebar-section">Reference</div>')
            else:
                opener = section_opener.get(part)
                section_label = PART_LABELS[part]
                if opener is not None:
                    opener_md, _ = opener
                    opener_fname = out_name(opener_md)
                    active_cls = ' class="sidebar-section sidebar-section-active"' if opener_md == active_md else ' class="sidebar-section"'
                    items.append(f'    <div{active_cls}><a href="{opener_fname}">{section_label}</a></div>')
                else:
                    items.append(f'    <div class="sidebar-section">{section_label}</div>')
            items.append('    <ul class="sidebar-list">')

        # Skip the part-opener entry in the list (it is linked via the section header above)
        if _is_part_opener_book5(section, num):
            continue

        fname = out_name(md_path)
        is_active = (md_path == active_md)
        active_cls = ' class="active"' if is_active else ""
        display = f"{num}. {label}" if num else label
        items.append(f'      <li><a href="{fname}"{active_cls}>{display}</a></li>')

    items.append("    </ul>")
    return "\n".join(items)

# ── page shell ────────────────────────────────────────────────────────────────

def page_shell(title: str, desc: str, fname: str, meta_line: str,
               sidebar: str, body: str, prev_link: str, next_link: str) -> str:
    nav_prev = f'<a class="prev" href="{prev_link[0]}">{prev_link[1]}</a>' if prev_link else ""
    nav_next = f'<a class="next" href="{next_link[0]}">{next_link[1]}</a>' if next_link else ""
    nav_row = f'  <div class="chapter-nav">{nav_prev}{nav_next}</div>' if (nav_prev or nav_next) else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)} &mdash; {SITE_TITLE}</title>
<meta name="description" content="{html.escape(desc[:160])}">
<link rel="canonical" href="{CANON}{fname}">
<link rel="stylesheet" href="styles.css">
<style>
  .sidebar-hub {{ margin-bottom: var(--space-4); padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--rule); font-size: 12px; font-family: var(--sans); }}
  .sidebar-hub a {{ color: var(--ink-muted); text-decoration: none; }}
  .sidebar-hub a:hover {{ color: var(--blue-deep); }}
  .sidebar-section a {{ color: inherit; text-decoration: none; }}
  .sidebar-section a:hover {{ color: var(--blue-deep); }}
  .sidebar-section-active a {{ color: var(--ink); }}
</style>
</head>
<body>
<div class="book">
  <aside class="sidebar">
{sidebar}
  </aside>
  <div class="main">
    <div class="chapter">
      <div class="chapter-meta">{meta_line}</div>
      {body}
{nav_row}
    </div>
  </div>
</div>
</body>
</html>"""

# ── generate all pages ────────────────────────────────────────────────────────

def generate():
    # Copy styles.css from book3 docs
    src_css = HERE.parent / "AgenticPMGuide" / "Web" / "docs" / "styles.css"
    shutil.copy(src_css, OUT / "styles.css")
    print(f"Copied styles.css")

    all_fnames = [out_name(p[0]) for p in PAGES]

    for idx, (md_path, label, section, num) in enumerate(PAGES):
        src = CHAPTERS / md_path
        if not src.exists():
            print(f"  MISSING: {src}"); continue

        md = src.read_text(encoding="utf-8")

        # Extract H1 title
        h1_match = re.search(r"^# (.+)$", md, re.MULTILINE)
        page_title = h1_match.group(1) if h1_match else label

        # Description: first real paragraph
        desc_match = re.search(r"^(?!#|>|-|\||\*)\S.+$", md, re.MULTILINE)
        desc = desc_match.group(0)[:200] if desc_match else label

        # Meta line
        if num:
            part_label = PART_LABELS.get(section, "")
            meta_line = f"{part_label} &nbsp;&middot;&nbsp; Chapter {num}"
        elif section.startswith("part"):
            meta_line = PART_LABELS.get(section, "")
        else:
            meta_line = "Reference"

        # Sidebar
        sidebar = build_sidebar(md_path)

        # Body (skip H1, rendered in shell)
        body_md = re.sub(r"^# .+\n", "", md, count=1)
        body_html = f'      <h1>{inline(html.unescape(page_title))}</h1>\n' + render_body(body_md)

        # Prev / next
        prev_link = (all_fnames[idx-1], PAGES[idx-1][1]) if idx > 0 else None
        next_link = (all_fnames[idx+1], PAGES[idx+1][1]) if idx < len(PAGES)-1 else None

        fname = out_name(md_path)
        html_out = page_shell(page_title, desc, fname, meta_line,
                              sidebar, body_html, prev_link, next_link)
        (OUT / fname).write_text(html_out, encoding="utf-8")
        print(f"  {fname}")

    # Generate index.html for book5
    generate_index()
    print("Done. Output: book5/")


def generate_index():
    toc_cards = []
    for md_path, label, section, num in PAGES:
        if section == "ref": continue
        fname = out_name(md_path)
        num_str = str(num) if num else ""
        part_label = PART_LABELS.get(section, "")
        toc_cards.append(f"""    <div class="toc-card">
      <a href="{fname}">
        <div class="toc-num">{part_label}{(" &middot; Ch. " + num_str) if num_str else ""}</div>
        <div class="toc-title">{html.escape(label)}</div>
      </a>
    </div>""")

    idx_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_TITLE} &mdash; {SITE_SUB}</title>
<meta name="description" content="How agentic AI reshapes the roles that build it. Seven parts on the team behind the agent: who owns what, where the hand-offs fail, and what the prior frameworks got wrong about shared responsibility.">
<link rel="canonical" href="{CANON}">
<link rel="stylesheet" href="styles.css">
<style>
  body {{ font-family: var(--serif); }}
  .landing {{ max-width: 880px; margin: 0 auto; padding: var(--space-8) var(--space-6); }}
  .landing-hero {{ padding: var(--space-7) 0 var(--space-6); border-bottom: 1px solid var(--rule); margin-bottom: var(--space-7); }}
  .landing-eyebrow {{ font-family: var(--sans); font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: var(--space-3); }}
  .landing-back {{ font-family: var(--sans); font-size: 13px; color: var(--ink-muted); margin-bottom: var(--space-4); }}
  .landing-back a {{ color: var(--blue-deep); text-decoration: none; }}
  .landing-back a:hover {{ text-decoration: underline; }}
  .landing-title {{ font-family: var(--serif); font-size: 44px; font-weight: 700; line-height: 1.1; color: var(--ink); margin-bottom: var(--space-3); }}
  .landing-subtitle {{ font-family: var(--serif); font-size: 22px; font-weight: 400; line-height: 1.3; color: var(--ink-soft); margin-bottom: var(--space-4); font-style: italic; }}
  .landing-byline {{ font-family: var(--sans); font-size: 14px; color: var(--ink-muted); }}
  .landing-byline a {{ color: var(--blue-deep); text-decoration: none; }}
  .landing-section {{ margin-bottom: var(--space-7); }}
  .landing-section h2 {{ font-family: var(--serif); font-size: 24px; font-weight: 600; margin-bottom: var(--space-4); color: var(--ink); border: none; padding: 0; }}
  .landing-section p {{ font-size: 18px; line-height: 1.65; color: var(--ink); margin-bottom: var(--space-4); }}
  .toc-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-3) var(--space-5); margin: var(--space-5) 0; }}
  .toc-card {{ padding: var(--space-3) var(--space-4); border: 0.5px solid var(--rule); border-radius: var(--radius-md); background: var(--bg); }}
  .toc-card a {{ color: var(--ink); text-decoration: none; display: block; }}
  .toc-card a:hover {{ color: var(--blue-deep); }}
  .toc-num {{ font-family: var(--sans); font-size: 11px; font-weight: 500; color: var(--ink-muted); letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 2px; }}
  .toc-title {{ font-family: var(--serif); font-size: 16px; font-weight: 500; line-height: 1.3; }}
  .cta-row {{ display: flex; gap: var(--space-3); flex-wrap: wrap; margin: var(--space-5) 0; }}
  .cta-btn {{ padding: var(--space-3) var(--space-5); font-family: var(--sans); font-size: 14px; font-weight: 500; border-radius: var(--radius-md); text-decoration: none; transition: all 0.15s; border: 1px solid var(--ink); }}
  .cta-primary {{ background: var(--ink); color: var(--bg); }}
  .cta-primary:hover {{ background: var(--ink-soft); }}
  .cta-secondary {{ background: transparent; color: var(--ink); }}
  .cta-secondary:hover {{ background: var(--tint-warm); }}
  .landing-footer {{ margin-top: var(--space-8); padding-top: var(--space-5); border-top: 1px solid var(--rule); font-family: var(--sans); font-size: 13px; color: var(--ink-muted); }}
  .landing-footer a {{ color: var(--blue-deep); text-decoration: none; }}
  @media (max-width: 720px) {{ .toc-grid {{ grid-template-columns: 1fr; }} .landing-title {{ font-size: 32px; }} }}
</style>
</head>
<body>
<div class="landing">
  <div class="landing-hero">
    <div class="landing-back"><a href="{HUB}">&larr; The Agentic AI Series</a></div>
    <div class="landing-eyebrow">Book 3 in the series{" &nbsp;&middot;&nbsp; Draft" if DRAFT else ""}</div>
    <h1 class="landing-title">{SITE_TITLE}</h1>
    <p class="landing-subtitle">{SITE_SUB}</p>
    <div class="landing-byline">By <a href="https://www.linkedin.com/in/yoram-friedman/" target="_blank" rel="noopener">Yoram Friedman</a></div>
  </div>

  <div class="landing-section">
    <p>The prior books in this series were written from the PM&rsquo;s seat. This one zooms out. The agentic shift does not invent shared responsibility; it evolves an already-shared model. This book takes every responsibility the first two books handed to the PM and redistributes it to the whole team: who really owns it, what slice the PM keeps, and where the hand-off fails.</p>
    <p>The unit of failure is the seam between roles, not the capability of any one of them. Seven parts, 26 chapters, and a seam audit appendix that maps every failure to the gap nobody owned.</p>
    <div class="cta-row">
      <a class="cta-btn cta-primary" href="what-youre-building.html">Start reading &rarr;</a>
      <a class="cta-btn cta-secondary" href="https://a.co/d/0jhGrB91" target="_blank" rel="noopener">Buy on Amazon</a>
    </div>
  </div>

  <div class="landing-section">
    <h2>Contents</h2>
    <div class="toc-grid">
{"".join(toc_cards)}
    </div>
  </div>

  <footer class="landing-footer">
    <p>Free to read online. &copy; 2026 Yoram Friedman. All rights reserved. &nbsp;&middot;&nbsp; <a href="{HUB}">All Books</a></p>
  </footer>
</div>
</body>
</html>"""
    (OUT / "index.html").write_text(idx_html, encoding="utf-8")
    print("  index.html")


if __name__ == "__main__":
    generate()
