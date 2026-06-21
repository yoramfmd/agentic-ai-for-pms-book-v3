#!/usr/bin/env python3
"""
build_web_book4.py — generate the web edition of Why Agentic AI Products Fail.

Source: Books/AgenticFailure/MANUSCRIPT-v4.0-FULL-current-2026-05-31.md  (single file)
Output: series-web/book4/  (flat HTML, GitHub Pages ready)

Run from the series-web/ directory:
    python3 build_web_book4.py
"""
from __future__ import annotations
import re, html, shutil
from pathlib import Path

HERE       = Path(__file__).resolve().parent
MANUSCRIPT = HERE.parent / "AgenticFailure" / "MANUSCRIPT-v4.0-FULL-current-2026-05-31.md"
OUT        = HERE / "book4"
OUT.mkdir(exist_ok=True)

SITE_TITLE = "Why Agentic AI Products Fail"
SITE_SUB   = "Building Channel 1 and the Supervisory Layer That Governs It"
CANON      = "https://agenticaiproductmanagement.com/book4/"
HUB        = "../index.html"

# Manual chapter registry — (slug, sidebar-label, section, display-num)
# section: "front" | "partN" | "back"
# Matches H1 titles in the manuscript
PAGES = [
    ("preface",                "Preface: The Job Did Not Shrink. It Shifted.",      "front",  None),
    ("field-snapshot",         "How the Job Actually Changed: A Field Snapshot",    "front",  None),
    ("two-channels",           "The Two Channels",                                  "front",  None),
    # Part I
    ("ch01-ai-literacy",       "What You Need to Know About AI",                    "part1",  1),
    ("ch02-not-a-bridge",      "You Are Not a Bridge Anymore",                      "part1",  2),
    ("ch03-not-every-problem", "Not Every Problem Deserves an Agent",               "part1",  3),
    # Part II
    ("ch04-how-work-splits",   "How the Work Splits",                               "part2",  4),
    ("ch05-vibe-coding",       "Vibe Coding for Value: Prototyping to Decide",      "part2",  5),
    ("ch06-collaborator",      "The PM as Collaborator",                            "part2",  6),
    # Part III
    ("ch07-design-behavior",   "You Built the Agent. Now Design the Behavior",      "part3",  7),
    ("ch08-two-hitl",          "Two Kinds of Human-in-the-Loop",                    "part3",  8),
    ("ch09-evals",             "Evals: What the Checkmarks Prove",                  "part3",  9),
    # Part IV
    ("ch10-guardrails",        "Operational Guardrails",                            "part4",  10),
    ("ch11-observation",       "You Can’t Measure What You Didn’t Design","part4",  11),
    ("ch12-record-complete",   "The Record Is Complete. The Picture Is Wrong.",     "part4",  12),
    ("ch13-silent-degradation","Silent Degradation",                                "part4",  13),
    ("ch14-audit-trails",      "Audit Trails That Survive the Agent",               "part4",  14),
    # Part V
    ("ch15-deference",         "Deference: The Problem After Capability",           "part5",  15),
    ("ch16-change-management", "Change Management: From Actor to Supervisor",       "part5",  16),
    ("ch17-hitl-fails",        "Why Human-in-the-Loop Fails",                       "part5",  17),
    ("ch18-skill-erosion",     "Skill Erosion: Deskilling, Never-Skilling, Cognitive Surrender", "part5", 18),
    ("ch19-team-member",       "The Agent Is a Team Member Nobody Hired",           "part5",  19),
    # Part VI
    ("ch20-people-never-seen", "What You Owe the People Your Agent Never Sees",     "part6",  20),
    ("ch21-governance",        "Agent Behavior Governance",                         "part6",  21),
    ("ch22-day-in-life",       "A Day in the Life of the Agentic PM",               "part6",  22),
    # Back matter
    ("agent-note",             "The Agent This Book Was Written With",              "back",   None),
    ("appendix-a",             "Appendix A: The Two Briefs, Worked",                "back",   None),
    ("appendix-b",             "Appendix B: The Field Manual",                      "back",   None),
    ("glossary",               "Glossary",                                          "back",   None),
    ("references",             "References and Sources",                            "back",   None),
]

PART_LABELS = {
    "front": "Front Matter",
    "part1": "Part I · Decide",
    "part2": "Part II · Prototype & Collaborate",
    "part3": "Part III · Design",
    "part4": "Part IV · Operate",
    "part5": "Part V · The Human System",
    "part6": "Part VI · Carry the Weight",
    "back":  "Back Matter",
}

# Map slug → filename
def fname(slug: str) -> str:
    return slug + ".html"

def slug_fn(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:60] or "section"

# ── inline markdown → HTML ────────────────────────────────────────────────────

def inline(s: str) -> str:
    # Apply markdown substitutions BEFORE html.escape so angle brackets in output are valid
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    # Escape only the non-tag portions
    def escape_text_nodes(t):
        return re.sub(r"(?<=>)([^<]+)(?=<)|^([^<]+)(?=<)|(?<=>)([^<]+)$|^([^<]+)$",
                      lambda m: html.escape(m.group(0), quote=False), t)
    s = escape_text_nodes(s)
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

    while i < n:
        raw = lines[i]; s = raw.strip()

        if s.startswith("<!--"): i += 1; continue
        if not s: i += 1; continue
        # Skip part headers (# PART I: ...) — they appear as section dividers in the single file
        if re.match(r"^# PART [IVX]+:", s): i += 1; continue
        # Skip H1 — handled by shell
        if re.match(r"^# [^#]", s): i += 1; continue
        # H2
        if s.startswith("## "):
            t = s[3:]; out.append(f'    <h2 id="{slug_fn(t)}">{inline(t)}</h2>'); i += 1; continue
        # H3
        if s.startswith("### "):
            t = s[4:]; out.append(f'    <h3 id="{slug_fn(t)}">{inline(t)}</h3>'); i += 1; continue
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
            if re.search(r"keep in your pocket", inner_md, re.IGNORECASE):
                pocket_out = ['    <div class="callout callout-pocket">',
                              '      <div class="callout-label">Keep in your pocket</div>']
                pocket_out.append("      " + render_body(
                    re.sub(r"\*\*keep in your pocket\*\*\n?", "", inner_md, flags=re.IGNORECASE).strip()
                ).strip())
                pocket_out.append("    </div>")
                pocket_html = "\n".join(pocket_out)
            else:
                first = inner_lines[0] if inner_lines else ""
                if re.match(r"^\*\*.+\*\*", first.strip()):
                    title = re.sub(r"\*\*(.+?)\*\*", r"\1", first.strip(), count=1)
                    rest_md = "\n".join(inner_lines[1:])
                    out.append('    <div class="callout">')
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
            for it in items: out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ul>")
            continue
        # Ordered list
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[i].strip())); i += 1
            out.append("    <ol>")
            for it in items: out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ol>")
            continue
        # Paragraph
        para_lines = []
        while i < n and lines[i].strip() and not lines[i].strip().startswith(("#", ">", "|")) \
              and not re.match(r"^-{3,}$", lines[i].strip()) \
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

# ── split single manuscript into chapter blobs ────────────────────────────────

def split_manuscript(text: str) -> dict[str, str]:
    """
    Split manuscript on H1 headings. Returns {slug: markdown_text} keyed to PAGES slugs.
    Uses a direct H1-title → slug lookup built from the exact manuscript H1 titles.
    """
    # Exact H1 title (as it appears in manuscript) → slug
    H1_TO_SLUG = {
        "Preface: The Job Did Not Shrink. It Shifted.":             "preface",
        "How the Job Actually Changed: A Field Snapshot":           "field-snapshot",
        "The Two Channels":                                          "two-channels",
        "Chapter 1: What You Need to Know About AI":                "ch01-ai-literacy",
        "Chapter 2: You Are Not a Bridge Anymore":                  "ch02-not-a-bridge",
        "Chapter 3: Not Every Problem Deserves an Agent":           "ch03-not-every-problem",
        "Chapter 4: How the Work Splits":                           "ch04-how-work-splits",
        "Chapter 5: Vibe Coding for Value: Prototyping to Decide":  "ch05-vibe-coding",
        "Chapter 6: The PM as Collaborator: Dev, UX, and Domain Experts": "ch06-collaborator",
        "Chapter 7: You Built the Agent. Now Design the Behavior":  "ch07-design-behavior",
        "Chapter 8: Two Kinds of Human-in-the-Loop":                "ch08-two-hitl",
        "Chapter 9: Evals: What the Checkmarks Prove":              "ch09-evals",
        "Chapter 10: Operational Guardrails: Budgets, Ceilings, Kill-Switches": "ch10-guardrails",
        "Chapter 11: You Can’t Measure What You Didn’t Design": "ch11-observation",
        "Chapter 11: You Can't Measure What You Didn't Design":     "ch11-observation",
        "Chapter 12: The Record Is Complete. The Picture Is Wrong.":"ch12-record-complete",
        "Chapter 13: Silent Degradation":                           "ch13-silent-degradation",
        "Chapter 14: Audit Trails That Survive the Agent":          "ch14-audit-trails",
        "Chapter 15: Deference: The Problem After Capability":      "ch15-deference",
        "Chapter 16: Change Management: From Actor to Supervisor":  "ch16-change-management",
        "Chapter 17: Why Human-in-the-Loop Fails":                  "ch17-hitl-fails",
        "Chapter 18: Skill Erosion: Deskilling, Never-Skilling, Cognitive Surrender": "ch18-skill-erosion",
        "Chapter 19: The Agent Is a Team Member Nobody Hired":      "ch19-team-member",
        "Chapter 20: What You Owe the People Your Agent Never Sees":"ch20-people-never-seen",
        "Chapter 21: Agent Behavior Governance":                    "ch21-governance",
        "Chapter 22: A Day in the Life of the Agentic PM":          "ch22-day-in-life",
        "The Agent This Book Was Written With":                     "agent-note",
        "Appendix A: The Two Briefs, Worked":                       "appendix-a",
        "Appendix B: The Field Manual":                             "appendix-b",
        "Glossary":                                                  "glossary",
        "References and Sources":                                   "references",
    }

    # Split on every H1
    parts = re.split(r"^(# .+)$", text, flags=re.MULTILINE)
    chapters: dict[str, str] = {}
    i = 1
    while i < len(parts) - 1:
        h1_line  = parts[i].strip()
        body     = parts[i+1] if i+1 < len(parts) else ""
        h1_title = h1_line[2:].strip()   # strip leading "# "

        slug = H1_TO_SLUG.get(h1_title)
        if slug:
            chapters[slug] = h1_line + "\n" + body
        i += 2

    return chapters

# ── sidebar ───────────────────────────────────────────────────────────────────

def build_sidebar(active_slug: str) -> str:
    items = []
    items.append(f'    <div class="sidebar-hub"><a href="{HUB}">&larr; All Books</a></div>')
    items.append(f'    <div class="sidebar-brand"><a href="index.html">{SITE_TITLE}</a>'
                 f'<div class="sidebar-brand-sub">{SITE_SUB}</div></div>')

    current_section = None
    list_open = False
    for (sl, label, section, num) in PAGES:
        if section != current_section:
            if list_open:
                items.append("    </ul>")
            current_section = section
            items.append(f'    <div class="sidebar-section">{PART_LABELS.get(section, section)}</div>')
            items.append('    <ul class="sidebar-list">')
            list_open = True
        is_active = (sl == active_slug)
        active_cls = ' class="active"' if is_active else ""
        display = f"{num}. {label}" if num else label
        items.append(f'      <li><a href="{fname(sl)}"{active_cls}>{display}</a></li>')
    if list_open:
        items.append("    </ul>")
    return "\n".join(items)

# ── page shell ────────────────────────────────────────────────────────────────

def page_shell(title, desc, sl, meta_line, sidebar, body, prev_link, next_link):
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
<link rel="canonical" href="{CANON}{fname(sl)}">
<link rel="stylesheet" href="styles.css">
<style>
  .sidebar-hub {{ margin-bottom: var(--space-4); padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--rule); font-size: 12px; font-family: var(--sans); }}
  .sidebar-hub a {{ color: var(--ink-muted); text-decoration: none; }}
  .sidebar-hub a:hover {{ color: var(--blue-deep); }}
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

# ── generate ──────────────────────────────────────────────────────────────────

def generate():
    src_css = HERE.parent / "AgenticPMGuide" / "Web" / "docs" / "styles.css"
    shutil.copy(src_css, OUT / "styles.css")
    print("Copied styles.css")

    text = MANUSCRIPT.read_text(encoding="utf-8")
    chapters = split_manuscript(text)
    print(f"Manuscript split: {len(chapters)} chapters matched")

    all_slugs = [p[0] for p in PAGES]

    for idx, (sl, label, section, num) in enumerate(PAGES):
        md = chapters.get(sl)
        if not md:
            print(f"  NOT MATCHED: {sl} ({label})")
            # Create a placeholder
            md = f"# {label}\n\n*Content coming soon.*\n"

        # Extract H1
        h1_match = re.search(r"^# (.+)$", md, re.MULTILINE)
        page_title = h1_match.group(1) if h1_match else label

        # Description: first real paragraph after H1
        body_only = re.sub(r"^# .+\n", "", md, count=1)
        desc_match = re.search(r"^(?!#|>|-|\|)\S.+$", body_only, re.MULTILINE)
        desc = (desc_match.group(0)[:200] if desc_match else label)

        # Meta line
        if num:
            meta_line = f"{PART_LABELS.get(section, '')} &nbsp;&middot;&nbsp; Chapter {num}"
        elif section == "front":
            meta_line = "Front Matter"
        else:
            meta_line = PART_LABELS.get(section, "")

        sidebar = build_sidebar(sl)

        # Render body (skip H1)
        body_md = re.sub(r"^# .+\n", "", md, count=1)
        body_html = f'      <h1>{inline(html.unescape(page_title))}</h1>\n' + render_body(body_md)

        prev_link = (fname(all_slugs[idx-1]), PAGES[idx-1][1]) if idx > 0 else None
        next_link = (fname(all_slugs[idx+1]), PAGES[idx+1][1]) if idx < len(PAGES)-1 else None

        html_out = page_shell(page_title, desc, sl, meta_line, sidebar,
                              body_html, prev_link, next_link)
        (OUT / fname(sl)).write_text(html_out, encoding="utf-8")
        print(f"  {fname(sl)}")

    generate_index()
    print("Done. Output: book4/")


def generate_index():
    toc_cards = []
    for sl, label, section, num in PAGES:
        if section in ("back",): continue
        num_str = str(num) if num else ""
        part_label = PART_LABELS.get(section, "")
        toc_cards.append(f"""    <div class="toc-card">
      <a href="{fname(sl)}">
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
<meta name="description" content="Every agentic product is two products: the agent that acts, and the supervisory layer that governs it. This book is about the supervisory layer, its four dimensions, its failure modes, and how to build it deliberately.">
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
    <div class="landing-eyebrow">Book 2 in the series</div>
    <h1 class="landing-title">{SITE_TITLE}</h1>
    <p class="landing-subtitle">{SITE_SUB}</p>
    <div class="landing-byline">By <a href="https://www.linkedin.com/in/yoram-friedman/" target="_blank" rel="noopener">Yoram Friedman</a></div>
  </div>

  <div class="landing-section">
    <p>Every agentic product is two products: the agent that acts, and the supervisory layer that governs it. Most teams build the first and assume the second takes care of itself. It does not. This book is organized around the supervisory layer, its four dimensions (technical, organizational, regulatory, and moral), its failure modes, and the discipline required to build it deliberately.</p>
    <p>Twenty-two chapters across six parts, from deciding whether to build at all to carrying accountability for the people your agent will never see.</p>
    <div class="cta-row">
      <a class="cta-btn cta-primary" href="preface.html">Start reading &rarr;</a>
      <a class="cta-btn cta-secondary" href="https://www.amazon.com/dp/B0F7LF1YLS" target="_blank" rel="noopener">Buy on Amazon</a>
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
