#!/usr/bin/env python3
"""
gen_backmatter.py — generate the 4 missing back-matter pages for book4.
Run from series-web/:  python3 gen_backmatter.py
Source: ../AgenticFailure/MANUSCRIPT-v4.0-FULL-current-2026-05-31.md
Output: book4/appendix-a.html, book4/appendix-b.html, book4/glossary.html, book4/references.html
"""
import re, html
from pathlib import Path

HERE       = Path(__file__).resolve().parent
MANUSCRIPT = HERE.parent / "AgenticFailure" / "MANUSCRIPT-v4.0-FULL-current-2026-05-31.md"
OUT        = HERE / "book4"
SITE_TITLE = "Why Agentic AI Products Fail"
SITE_SUB   = "Building Channel 1 and the Supervisory Layer That Governs It"
CANON      = "https://agenticaiproductmanagement.com/book4/"
HUB        = "../index.html"

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

ALL_PAGES = [
    ("preface",               "Preface: The Job Did Not Shrink. It Shifted.",                       "front", None),
    ("field-snapshot",        "How the Job Actually Changed: A Field Snapshot",                     "front", None),
    ("two-channels",          "The Two Channels",                                                   "front", None),
    ("ch01-ai-literacy",      "What You Need to Know About AI",                                     "part1", 1),
    ("ch02-not-a-bridge",     "You Are Not a Bridge Anymore",                                       "part1", 2),
    ("ch03-not-every-problem","Not Every Problem Deserves an Agent",                                "part1", 3),
    ("ch04-how-work-splits",  "How the Work Splits",                                                "part2", 4),
    ("ch05-vibe-coding",      "Vibe Coding for Value: Prototyping to Decide",                       "part2", 5),
    ("ch06-collaborator",     "The PM as Collaborator",                                             "part2", 6),
    ("ch07-design-behavior",  "You Built the Agent. Now Design the Behavior",                       "part3", 7),
    ("ch08-two-hitl",         "Two Kinds of Human-in-the-Loop",                                     "part3", 8),
    ("ch09-evals",            "Evals: What the Checkmarks Prove",                                   "part3", 9),
    ("ch10-guardrails",       "Operational Guardrails",                                             "part4", 10),
    ("ch11-observation",      "You Can't Measure What You Didn't Design",                           "part4", 11),
    ("ch12-record-complete",  "The Record Is Complete. The Picture Is Wrong.",                      "part4", 12),
    ("ch13-silent-degradation","Silent Degradation",                                                "part4", 13),
    ("ch14-audit-trails",     "Audit Trails That Survive the Agent",                                "part4", 14),
    ("ch15-deference",        "Deference: The Problem After Capability",                            "part5", 15),
    ("ch16-change-management","Change Management: From Actor to Supervisor",                        "part5", 16),
    ("ch17-hitl-fails",       "Why Human-in-the-Loop Fails",                                       "part5", 17),
    ("ch18-skill-erosion",    "Skill Erosion: Deskilling, Never-Skilling, Cognitive Surrender",    "part5", 18),
    ("ch19-team-member",      "The Agent Is a Team Member Nobody Hired",                            "part5", 19),
    ("ch20-people-never-seen","What You Owe the People Your Agent Never Sees",                      "part6", 20),
    ("ch21-governance",       "Agent Behavior Governance",                                          "part6", 21),
    ("ch22-day-in-life",      "A Day in the Life of the Agentic PM",                               "part6", 22),
    ("agent-note",            "The Agent This Book Was Written With",                               "back",  None),
    ("appendix-a",            "Appendix A: The Two Briefs, Worked",                                 "back",  None),
    ("appendix-b",            "Appendix B: The Field Manual",                                       "back",  None),
    ("glossary",              "Glossary",                                                            "back",  None),
    ("references",            "References and Sources",                                             "back",  None),
]

H1_TO_SLUG = {
    "Appendix A: The Two Briefs, Worked": "appendix-a",
    "Appendix B: The Field Manual":        "appendix-b",
    "Glossary":                            "glossary",
    "References and Sources":             "references",
}

def fname(slug): return slug + ".html"

def slug_fn(t):
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"[^\w\s-]", "", t).strip().lower()
    return re.sub(r"[\s_]+", "-", t)[:60] or "section"

def inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    def esc(t):
        return re.sub(r"(?<=>)([^<]+)(?=<)|^([^<]+)(?=<)|(?<=>)([^<]+)$|^([^<]+)$",
                      lambda m: html.escape(m.group(0), quote=False), t)
    s = esc(s)
    out = []; opn = True
    for ch in s:
        if ch == '"':
            out.append("&ldquo;" if opn else "&rdquo;"); opn = not opn
        else:
            out.append(ch)
    s = "".join(out)
    s = re.sub(r"(\w)'(\w)", r"\1&rsquo;\2", s)
    s = re.sub(r"(?<=\w)'", "&rsquo;", s)
    return s.replace("'", "&lsquo;")

def render_body(md):
    lines = md.split("\n"); out = []; i = 0; n = len(lines)
    def ptable(tbl):
        rows = [r for r in tbl if r.strip().startswith("|")]
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
        if not s or s.startswith("<!--") or re.match(r"^# ", s): i += 1; continue
        if s.startswith("## "):
            t = s[3:]; out.append(f'    <h2 id="{slug_fn(t)}">{inline(t)}</h2>'); i += 1; continue
        if s.startswith("### "):
            t = s[4:]; out.append(f'    <h3 id="{slug_fn(t)}">{inline(t)}</h3>'); i += 1; continue
        if re.match(r"^-{3,}$", s):
            out.append("    <hr>"); i += 1; continue
        if s.startswith("|"):
            tbl = []
            while i < n and lines[i].strip().startswith("|"): tbl.append(lines[i]); i += 1
            out.append(ptable(tbl)); continue
        if s.startswith(">"):
            block = []
            while i < n and (lines[i].strip().startswith(">") or (block and not lines[i].strip())):
                block.append(lines[i]); i += 1
            inner = [re.sub(r"^>\s?", "", bl) for bl in block if bl.strip()]
            first = inner[0] if inner else ""
            if re.match(r"^\*\*.+\*\*", first.strip()):
                title = re.sub(r"\*\*(.+?)\*\*", r"\1", first.strip(), count=1)
                out.append('    <div class="callout">')
                out.append(f'      <div class="callout-title">{inline(title)}</div>')
                out.append("      " + render_body("\n".join(inner[1:])).strip())
                out.append("    </div>")
            else:
                bq = "\n".join(f"<p>{inline(l)}</p>" for l in inner if l.strip())
                out.append(f"    <blockquote>{bq}</blockquote>")
            continue
        if re.match(r"^[-*+]\s", s):
            items = []
            while i < n and re.match(r"^[-*+]\s", lines[i].strip()):
                items.append(lines[i].strip()[2:]); i += 1
            out.append("    <ul>")
            for it in items: out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ul>"); continue
        if re.match(r"^\d+\.\s", s):
            items = []
            while i < n and re.match(r"^\d+\.\s", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[i].strip())); i += 1
            out.append("    <ol>")
            for it in items: out.append(f"      <li>{inline(it)}</li>")
            out.append("    </ol>"); continue
        para = []
        while i < n and lines[i].strip() \
              and not lines[i].strip().startswith(("#", ">", "|")) \
              and not re.match(r"^-{3,}$", lines[i].strip()) \
              and not re.match(r"^[-*+]\s", lines[i].strip()) \
              and not re.match(r"^\d+\.\s", lines[i].strip()):
            para.append(lines[i].strip()); i += 1
        text = " ".join(para)
        if text: out.append(f"    <p>{inline(text)}</p>")
    return "\n".join(out)

def build_sidebar(active_slug):
    items = [
        f'    <div class="sidebar-hub"><a href="{HUB}">&larr; All Books</a></div>',
        f'    <div class="sidebar-brand"><a href="index.html">{SITE_TITLE}</a>'
        f'<div class="sidebar-brand-sub">{SITE_SUB}</div></div>',
    ]
    cur = None; list_open = False
    for sl, label, section, num in ALL_PAGES:
        if section != cur:
            if list_open: items.append("    </ul>")
            cur = section
            items.append(f'    <div class="sidebar-section">{PART_LABELS.get(section, section)}</div>')
            items.append('    <ul class="sidebar-list">'); list_open = True
        ac = ' class="active"' if sl == active_slug else ""
        disp = f"{num}. {label}" if num else label
        items.append(f'      <li><a href="{fname(sl)}"{ac}>{disp}</a></li>')
    if list_open: items.append("    </ul>")
    return "\n".join(items)

def page_shell(title, desc, sl, sidebar, body, prev_link, next_link):
    nav_prev = f'<a class="prev" href="{prev_link[0]}">{prev_link[1]}</a>' if prev_link else ""
    nav_next = f'<a class="next" href="{next_link[0]}">{next_link[1]}</a>' if next_link else ""
    nav_row  = f'  <div class="chapter-nav">{nav_prev}{nav_next}</div>' if (nav_prev or nav_next) else ""
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
      <div class="chapter-meta">Back Matter</div>
      {body}
{nav_row}
    </div>
  </div>
</div>
</body>
</html>"""

def generate():
    print(f"Reading manuscript…")
    text = MANUSCRIPT.read_text(encoding="utf-8")
    parts = re.split(r"^(# .+)$", text, flags=re.MULTILINE)
    chapters = {}
    i = 1
    while i < len(parts) - 1:
        h1_title = parts[i][2:].strip()
        slug = H1_TO_SLUG.get(h1_title)
        if slug:
            chapters[slug] = parts[i] + "\n" + parts[i+1]
        i += 2
    print(f"Matched: {list(chapters.keys())}")

    all_slugs = [p[0] for p in ALL_PAGES]

    for target in ["appendix-a", "appendix-b", "glossary", "references"]:
        md = chapters.get(target)
        if not md:
            print(f"  WARNING: no content matched for {target}"); continue
        idx = next(j for j, p in enumerate(ALL_PAGES) if p[0] == target)
        sl, label, section, num = ALL_PAGES[idx]
        h1m = re.search(r"^# (.+)$", md, re.MULTILINE)
        page_title = h1m.group(1) if h1m else label
        body_only  = re.sub(r"^# .+\n", "", md, count=1)
        dm         = re.search(r"^(?!#|>|-|\|)\S.+$", body_only, re.MULTILINE)
        desc       = dm.group(0)[:200] if dm else label
        sidebar    = build_sidebar(sl)
        bmd        = re.sub(r"^# .+\n", "", md, count=1)
        bhtml      = f'      <h1>{inline(html.unescape(page_title))}</h1>\n' + render_body(bmd)
        prev       = (fname(all_slugs[idx-1]), ALL_PAGES[idx-1][1]) if idx > 0 else None
        nxt        = (fname(all_slugs[idx+1]), ALL_PAGES[idx+1][1]) if idx < len(ALL_PAGES)-1 else None
        out        = page_shell(page_title, desc, sl, sidebar, bhtml, prev, nxt)
        (OUT / fname(sl)).write_text(out, encoding="utf-8")
        print(f"  {fname(sl)}  ({len(out):,} chars)")

    print("Done.")

if __name__ == "__main__":
    generate()
