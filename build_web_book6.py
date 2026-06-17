#!/usr/bin/env python3
"""
build_web_book6.py — generate the web edition of The Agentic AI Practitioner.

Source: Books/AgenticPractitioner/BOOK4-FULL-DRAFT-v1.4-READING-COPY.md
         (single consolidated reading copy; split on H1 boundaries)
Output: series-web/book6/  (flat HTML, GitHub Pages ready)

Run from the series-web/ directory:
    python3 build_web_book6.py
"""
from __future__ import annotations
import re, html, shutil
from pathlib import Path

HERE      = Path(__file__).resolve().parent
SOURCE_MD = HERE.parent / "AgenticPractitioner" / "BOOK4-FULL-DRAFT-v1.4-READING-COPY.md"
OUT       = HERE / "book6"
OUT.mkdir(exist_ok=True)

SITE_TITLE = "The Agentic AI Practitioner"
SITE_SUB   = "Keeping the Judgment the Machine Cannot Hold"
CANON      = "https://agenticaiproductmanagement.com/book6/"
HUB        = "../index.html"

# Section assignment by H1 title. Keys are exact H1 strings.
# Values: (sidebar-label, section-key, display-num)
#   section-key controls the sidebar group; "skip" means do not render
SECTION_MAP = {
    "The Agentic AI Series, Book 4 (working title)": ("__skip__", "skip", None),
    "Preface: The Job Is Now the Person":            ("Preface", "front", None),
    "The Series in One Page":                        ("The Series in One Page", "front", None),
    # Part I
    "Part I: The Stakes":                            ("Part I: The Stakes", "part1", None),
    "Chapter 1: The Perishable Asset":               ("The Perishable Asset", "part1", 1),
    "Chapter 2: Not All Humans in the Loop Are the Same Human":
        ("Not All Humans in the Loop Are the Same Human", "part1", 2),
    "Chapter 3: The Apprenticeship You No Longer Get":
        ("The Apprenticeship You No Longer Get", "part1", 3),
    # Part II
    "Part II: The Practice":                         ("Part II: The Practice", "part2", None),
    "Chapter 4: Reps, Not Reading":                  ("Reps, Not Reading", "part2", 4),
    "Chapter 5: The Loop That Teaches You Back":     ("The Loop That Teaches You Back", "part2", 5),
    "Chapter 6: Reading the Actor Under the Costume":("Reading the Actor Under the Costume", "part2", 6),
    "Chapter 7: Configuration Is Self-Knowledge":    ("Configuration Is Self-Knowledge", "part2", 7),
    "Chapter 8: The Proficiency Check":              ("The Proficiency Check", "part2", 8),
    # Part III
    "Part III: The Craft":                           ("Part III: The Craft", "part3", None),
    "Chapter 9: The Brief as Craft":                 ("The Brief as Craft", "part3", 9),
    "Chapter 10: Eval Literacy for the Gate Owner":  ("Eval Literacy for the Gate Owner", "part3", 10),
    "Chapter 11: The Steady State":                  ("The Steady State", "part3", 11),
    "Chapter 12: Which Frameworks Still Hold":       ("Which Frameworks Still Hold", "part3", 12),
    "Chapter 13: Operating Inside the Org":          ("Operating Inside the Org", "part3", 13),
    # Part IV
    "Part IV: The Career":                           ("Part IV: The Career", "part4", None),
    "Chapter 14: The Role Landscape":                ("The Role Landscape", "part4", 14),
    "Chapter 15: No Certification for This":         ("No Certification for This", "part4", 15),
    # Back matter
    "The Practitioner's Record":                     ("The Practitioner's Record", "ref", None),
    "Appendix A: The Loop Templates":                ("A. The Loop Templates", "ref", None),
    "Appendix B: The Model Dossier":                 ("B. The Model Dossier", "ref", None),
    "Appendix C: The Proficiency Record":            ("C. The Proficiency Record", "ref", None),
    "Appendix D: The Two Briefs":                    ("D. The Two Briefs", "ref", None),
    "Appendix E: The Gate Owner's Checklist":        ("E. The Gate Owner's Checklist", "ref", None),
    "Appendix F: The Steady-State Page":             ("F. The Steady-State Page", "ref", None),
    "Appendix G: The Post-Mortem and Dissent Ledger":("G. The Post-Mortem and Dissent Ledger", "ref", None),
    "Appendix H: The First Month":                   ("H. The First Month", "ref", None),
    "Notes and Sources":                             ("Notes and Sources", "ref", None),
    "References":                                    ("References", "ref", None),
}

PART_LABELS = {
    "front":  "Front Matter",
    "part1":  "Part I · The Stakes",
    "part2":  "Part II · The Practice",
    "part3":  "Part III · The Craft",
    "part4":  "Part IV · The Career",
    "ref":    "Reference",
}

def slug_filename(title: str) -> str:
    """Convert an H1 title to a stable HTML filename."""
    t = title.lower()
    t = re.sub(r"^chapter\s+\d+:\s*", "", t)
    t = re.sub(r"^appendix\s+[a-h0-9]+:\s*", "", t)
    t = re.sub(r"^part\s+[ivxlc]+:\s*", "part-", t)
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"[\s_]+", "-", t.strip())
    t = re.sub(r"-+", "-", t)
    return (t[:60].rstrip("-") or "section") + ".html"


def split_into_pages(md: str):
    """Split the consolidated MD on H1 boundaries. Returns list of (title, body_md)."""
    # Find all H1 positions
    pattern = re.compile(r"(?m)^# (.+)$")
    matches = list(pattern.finditer(md))
    pages = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        body_start = m.end()
        body_end = matches[i+1].start() if i+1 < len(matches) else len(md)
        body = md[body_start:body_end].strip()
        pages.append((title, body))
    return pages


def slug(t: str) -> str:
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:60] or "section"

# ── inline markdown → HTML ────────────────────────────────────────────────────

def inline(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
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

# ── block parser (lifted from book5) ──────────────────────────────────────────

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

        # Skip any H1 inside the body (should not occur after split, but defensive)
        if s.startswith("# ") and not s.startswith("## ") and not s.startswith("### "):
            i += 1; continue

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

# ── sidebar ───────────────────────────────────────────────────────────────────

def _is_part_opener(entry):
    """A part-opener entry is one whose H1 starts with 'Part ' and has no chapter number."""
    return entry["h1"].startswith("Part ") and entry["num"] is None


def build_sidebar(active_fname: str, ordered_entries):
    items: list[str] = []
    items.append(f'    <div class="sidebar-hub"><a href="{HUB}">&larr; All Books</a></div>')
    items.append(f'    <div class="sidebar-brand"><a href="index.html">{SITE_TITLE}</a>'
                 f'<div class="sidebar-brand-sub">{SITE_SUB}</div></div>')

    # Map each section to its part-opener entry (if any), so we can link the section header to it.
    section_opener = {}
    for e in ordered_entries:
        if _is_part_opener(e):
            section_opener[e["section"]] = e

    current_section = None
    for entry in ordered_entries:
        section = entry["section"]
        if section != current_section:
            if current_section is not None:
                items.append("    </ul>")
            current_section = section
            opener = section_opener.get(section)
            label = PART_LABELS[section]
            if opener is not None:
                active_cls = ' class="sidebar-section sidebar-section-active"' if opener["fname"] == active_fname else ' class="sidebar-section"'
                items.append(f'    <div{active_cls}><a href="{opener["fname"]}">{label}</a></div>')
            else:
                items.append(f'    <div class="sidebar-section">{label}</div>')
            items.append('    <ul class="sidebar-list">')

        # Skip part-opener entries inside the list (they are linked via the section header above)
        if _is_part_opener(entry):
            continue

        fname = entry["fname"]
        is_active = (fname == active_fname)
        active_cls = ' class="active"' if is_active else ""
        display = f"{entry['num']}. {entry['label']}" if entry["num"] else entry["label"]
        items.append(f'      <li><a href="{fname}"{active_cls}>{display}</a></li>')

    items.append("    </ul>")
    return "\n".join(items)

# ── page shell ────────────────────────────────────────────────────────────────

def page_shell(title: str, desc: str, fname: str, meta_line: str,
               sidebar: str, body: str, prev_link, next_link) -> str:
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

# ── main generate ─────────────────────────────────────────────────────────────

def generate():
    # Copy styles.css from book3 docs (same source as book5)
    src_css = HERE.parent / "AgenticPMGuide" / "Web" / "docs" / "styles.css"
    shutil.copy(src_css, OUT / "styles.css")
    print(f"Copied styles.css")

    md = SOURCE_MD.read_text(encoding="utf-8")
    raw_pages = split_into_pages(md)
    print(f"Found {len(raw_pages)} H1 sections in source")

    # Filter against SECTION_MAP; emit warning for unknown
    entries = []
    for (title, body) in raw_pages:
        if title not in SECTION_MAP:
            print(f"  ! UNKNOWN H1 skipped: {title!r}")
            continue
        label, section, num = SECTION_MAP[title]
        if section == "skip":
            continue
        entries.append({
            "h1": title,
            "label": label,
            "section": section,
            "num": num,
            "fname": slug_filename(title),
            "body": body,
        })

    fnames = [e["fname"] for e in entries]
    for idx, e in enumerate(entries):
        body_md = e["body"]
        desc_match = re.search(r"^(?!#|>|-|\||\*)\S.+$", body_md, re.MULTILINE)
        desc = desc_match.group(0)[:200] if desc_match else e["label"]

        if e["num"]:
            meta_line = f"{PART_LABELS[e['section']]} &nbsp;&middot;&nbsp; Chapter {e['num']}"
        else:
            meta_line = PART_LABELS[e["section"]]

        sidebar = build_sidebar(e["fname"], entries)
        body_html = f'      <h1>{inline(html.unescape(e["h1"]))}</h1>\n' + render_body(body_md)

        prev_link = (fnames[idx-1], entries[idx-1]["label"]) if idx > 0 else None
        next_link = (fnames[idx+1], entries[idx+1]["label"]) if idx < len(entries)-1 else None

        html_out = page_shell(e["h1"], desc, e["fname"], meta_line,
                              sidebar, body_html, prev_link, next_link)
        (OUT / e["fname"]).write_text(html_out, encoding="utf-8")
        print(f"  {e['fname']}")

    generate_index(entries)
    print("Done. Output: book6/")


def generate_index(entries):
    toc_cards = []
    for e in entries:
        if e["section"] == "ref":
            continue
        if e["section"] == "front" and e["h1"] != "Preface: The Job Is Now the Person":
            continue
        num_str = f"Ch. {e['num']}" if e["num"] else ""
        part_label = PART_LABELS[e["section"]]
        meta = f"{part_label}{' &middot; ' + num_str if num_str else ''}"
        toc_cards.append(f"""    <div class="toc-card">
      <a href="{e['fname']}">
        <div class="toc-num">{meta}</div>
        <div class="toc-title">{html.escape(e['label'])}</div>
      </a>
    </div>""")

    idx_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_TITLE} &mdash; {SITE_SUB}</title>
<meta name="description" content="A deliberate-practice curriculum for AI product managers. How an individual PM builds and keeps the judgment the machine cannot hold.">
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
    <div class="landing-eyebrow">Book 4 in the series</div>
    <h1 class="landing-title">{SITE_TITLE}</h1>
    <p class="landing-subtitle">{SITE_SUB}</p>
    <div class="landing-byline">By <a href="https://www.linkedin.com/in/yoram-friedman/" target="_blank" rel="noopener">Yoram Friedman</a></div>
  </div>

  <div class="landing-section">
    <p>Book 1 gave the operating loop. Book 2 gave the failure modes. Book 3 gave the team and deliberately de-centered the PM. This book returns to the person in the seat without undoing that move: not PM-as-hero, but how to stay competent in the seat the team routes through.</p>
    <p>The series&rsquo; own evidence (Quiet Erosion, Supervision Paradox, cognitive surrender, validator atrophy) says the capability everything depends on is perishable. No book in the series until now teaches the maintenance program. Fifteen chapters and a full appendix set: a deliberate-practice curriculum grounded in deskilling evidence, modeled on aviation&rsquo;s mandatory no-automation proficiency checks.</p>
    <div class="cta-row">
      <a class="cta-btn cta-primary" href="preface-the-job-is-now-the-person.html">Start reading &rarr;</a>
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
