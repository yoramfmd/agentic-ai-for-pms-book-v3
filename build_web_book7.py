#!/usr/bin/env python3
"""
build_web_book7.py -- generate the web edition of Agentic AI for Product Leaders.

Source: books/OneBook/AGENTIC-AI-FOR-PRODUCT-LEADERS.md, the locked manuscript.
Output: series-web/book7/  (flat HTML, GitHub Pages ready)

Run from the series-web/ directory:
    python3 build_web_book7.py

WHY THIS ONE IS DIFFERENT FROM build_web_book{4,5,6}.py
-------------------------------------------------------
Those split the source on H1 boundaries. This manuscript has exactly one H1, its
title. Its structure is carried in heading depth instead: H2 for the divisions,
H3 for chapters and phases, H4 for sections and exhibits, H5 for cards. So this
builder splits on H3 and keeps H4/H5 inside the page, which is also what lets the
apparatus render inline.

AND IT FAILS LOUDLY, WHICH IS THE POINT
----------------------------------------
build_web_book6.py documents its own worst bug in a comment: "Unmapped H1s are
silently skipped, so the stale map would have dropped seven appendices from the
build without failing." It had been frozen at v1.4 for weeks because SOURCE_MD
pointed at a file that no longer existed.

This builder therefore asserts, and stops rather than shipping a partial book:
  * the source file exists and is the locked manuscript
  * every H3 in the source is in SECTION_MAP, or the build fails and names it
  * exactly 30 cards and 11 exhibits survive into the output
  * every output page is non-empty
A book that has gained a chapter should break this build. That is cheaper than a
web edition that quietly lost one.

PUBLISHING
----------
Nothing here commits or pushes. Per Yoram, 2026-08-24: written now, published
after the final lock. Run it, read book7/, and publish deliberately.
"""
from __future__ import annotations

import html
import re
import shutil
import sys
from pathlib import Path

from _bookpaths import book_source, shared_css  # single source of truth for where manuscripts live

HERE = Path(__file__).resolve().parent
SOURCE_MD = book_source("OneBook", "AGENTIC-AI-FOR-PRODUCT-LEADERS.md")
OUT = HERE / "book7"

SITE_TITLE = "Agentic AI for Product Leaders"
SITE_SUB = "One agent, one company, from the sentence that proposed it to the year after it launched"
CANON = "https://agenticaiproductmanagement.com/book7/"
HUB = "../index.html"
BOOK_DESC = (
    "The fifth book in the series, and the one built the other way: a single "
    "fictional company followed through five phases of building an agent, with "
    "the thirty procedure cards and eleven case-file exhibits the project produced."
)

# ---------------------------------------------------------------------------
# Section map. Key is the H3 heading text exactly as it appears in the source,
# minus the leading "### ". Value is (output filename, nav group, order).
#
# Anything in the source and not in here stops the build. Do not add a
# catch-all: the whole value of this table is that it is a second opinion about
# what the book contains.
# ---------------------------------------------------------------------------
CH = "chapter"
PH = "phase"
BACK = "back"

SECTION_MAP: dict[str, tuple[str, str, int]] = {
    "Chapter 1 · The person at the end of the path": ("the-person-at-the-end-of-the-path.html", CH, 1),
    "Chapter 2 · The people in the room": ("the-people-in-the-room.html", CH, 2),
    "Chapter 3 · The colleague nobody interviewed": ("the-colleague-nobody-interviewed.html", CH, 3),
    "Chapter 4 · What an agent actually is": ("what-an-agent-actually-is.html", CH, 4),
    "Chapter 5 · The floor and the plateau": ("the-floor-and-the-plateau.html", CH, 5),
    "Chapter 6 · The brain, the layers, the loop": ("the-brain-the-layers-the-loop.html", CH, 6),
    "Chapter 7 · The judgment gap and the paradox": ("the-judgment-gap-and-the-paradox.html", CH, 7),
    "Chapter 8 · The two products": ("the-two-products.html", CH, 8),
    "Chapter 9 · The new PM role, and what you actually build": ("the-new-pm-role.html", CH, 9),
    "Chapter 10 · The shape of the work": ("the-shape-of-the-work.html", CH, 10),
    "Phase 1 · Decide": ("decide.html", PH, 1),
    "Phase 2 · Design": ("design.html", PH, 2),
    "Phase 3 · Prove": ("prove.html", PH, 3),
    "Phase 4 · Observe": ("observe.html", PH, 4),
    "Phase 5 · Operate": ("operate.html", PH, 5),
}

# H2 divisions that become their own page rather than splitting into H3 units.
DIVISION_PAGES = {
    "Preface · Before you start": ("preface.html", "front", 0),
    "Coda · What to keep": ("coda.html", BACK, 1),
    "Appendix · Climbing: what changes as autonomy rises": ("appendix-climbing.html", BACK, 2),
    "Appendix · Five artifacts, blank": ("appendix-five-artifacts.html", BACK, 3),
    "Sources and status notes, by chapter": ("notes-and-sources.html", BACK, 4),
    # C93. The print edition carries a QR here; the web edition is already on
    # the web, so the page carries the link and the same tier statement.
    "The companion site": ("companion-site.html", BACK, 5),
}

# H2s that carry no body of their own: their H3 children are the pages.
CONTAINER_DIVISIONS = {"Part One", "Part Two"}
# H2s deliberately not published: the print contents list is replaced by the nav.
SKIP_DIVISIONS = {"Contents"}


# ---------------------------------------------------------------------------
# A small markdown renderer. The manuscript uses a deliberately narrow subset:
# headings, paragraphs, bold, italic, inline code, ordered and bullet lists,
# blockquotes, pipe tables and thematic breaks. Anything wider than that would
# be a change in the book, so this does not try to be general.
# ---------------------------------------------------------------------------
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
    return s


def slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-")


def render_table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    body = [r for r in cells if not all(set(c) <= set("-: ") for c in r)]
    if not body:
        return ""
    head, rest = body[0], body[1:]
    out = ['<div class="table-wrap"><table>', "<thead><tr>"]
    out += [f"<th>{inline(c)}</th>" for c in head]
    out.append("</tr></thead><tbody>")
    for r in rest:
        out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render_blocks(md: str, found: list | None = None) -> str:
    """Render one section's markdown body, apparatus included.

    If `found` is given, every card and exhibit is appended to it as
    (kind, name, anchor) so the landing page can list what each phase produced,
    the way the book's own plan page does.
    """
    lines = md.split("\n")
    out: list[str] = []
    i, n = 0, len(lines)
    open_wrapper: str | None = None

    def close_wrapper():
        nonlocal open_wrapper
        if open_wrapper:
            out.append("</div>")
            open_wrapper = None

    while i < n:
        line = lines[i]
        t = line.strip()

        if not t:
            i += 1
            continue

        if t == "---":
            close_wrapper()
            i += 1
            continue

        # H5 · a procedure card
        m = re.match(r"^#####\s+Card\s+·\s+(.+)$", t)
        if m:
            close_wrapper()
            anchor = "card-" + slug(m.group(1))
            if found is not None:
                found.append(("Card", m.group(1), anchor))
            out.append(f'<div class="callout" id="{anchor}">'
                       '<div class="callout-label">Card</div>'
                       f'<div class="callout-title">{inline(m.group(1))}</div>')
            open_wrapper = "card"
            i += 1
            continue

        # H4 · an exhibit, or an ordinary section head
        m = re.match(r"^####\s+(Exhibit\s+[A-K])\s+·\s+(.+)$", t)
        if m:
            close_wrapper()
            anchor = slug(m.group(1))
            if found is not None:
                found.append((m.group(1), m.group(2), anchor))
            out.append(f'<div class="callout" id="{anchor}">'
                       '<div class="callout-label">'
                       f'{inline(m.group(1))}</div>'
                       f'<div class="callout-title">{inline(m.group(2))}</div>')
            open_wrapper = "exhibit"
            i += 1
            continue
        m = re.match(r"^####\s+(.+)$", t)
        if m:
            close_wrapper()
            out.append(f"<h3>{inline(m.group(1))}</h3>")
            i += 1
            continue

        # blockquote: the Rule, or the phase-adds rail
        if t.startswith(">"):
            quote, j = [], i
            while j < n and lines[j].strip().startswith(">"):
                quote.append(lines[j].strip()[1:].strip())
                j += 1
            body = " ".join(x for x in quote if x)
            # Blockquotes in the manuscript carry four different things, and the
            # first version of this labelled all of them "In this phase", which
            # put that label on every gloss in the book. Yoram, 2026-08-24, with
            # a screenshot of the rung gloss wearing it.
            if body.startswith("**The Rule."):
                out.append(f'<div class="rule-line">{inline(body)}</div>')
            elif body.startswith("**Phase map"):
                closing = "closing" in body.split("**")[1].lower()
                label = "The phase, closing" if closing else "The phase"
                rest = body.split("**", 2)[-1].strip()
                out.append(f'<div class="card phase-rail"><div class="card-label">{label}</div>'
                           f'<div class="card-title">{inline(rest)}</div></div>')
            elif body.startswith("*") and ":" in body[:60]:
                # a gloss: *Term: definition*
                inner = body.strip("*").strip()
                term, _, definition = inner.partition(":")
                out.append(f'<div class="card gloss"><div class="card-label">{html.escape(term.strip())}</div>'
                           f'<div class="card-title">{inline(definition.strip())}</div></div>')
            else:
                out.append(f'<div class="card"><div class="card-title">{inline(body)}</div></div>')
            i = j
            continue

        # pipe table
        if t.startswith("|"):
            rows, j = [], i
            while j < n and lines[j].strip().startswith("|"):
                rows.append(lines[j])
                j += 1
            out.append(render_table(rows))
            i = j
            continue

        # ordered list
        if re.match(r"^\d+\.\s", t):
            items, j = [], i
            while j < n and re.match(r"^\d+\.\s", lines[j].strip()):
                items.append(re.sub(r"^\d+\.\s", "", lines[j].strip()))
                j += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            i = j
            continue

        # bullet list
        if re.match(r"^[-*]\s", t):
            items, j = [], i
            while j < n and re.match(r"^[-*]\s", lines[j].strip()):
                items.append(re.sub(r"^[-*]\s", "", lines[j].strip()))
                j += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            i = j
            continue

        # paragraph
        para, j = [], i
        while j < n and lines[j].strip() and not re.match(r"^(#{4,5}\s|>|\||[-*]\s|\d+\.\s|---$)", lines[j].strip()):
            para.append(lines[j].strip())
            j += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
        i = j

    close_wrapper()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
# The series stylesheet already carries the layout, the callout vocabulary and
# table styling. Only three things this book needs are missing from it, so only
# three things are added here. The first draft of this builder invented eleven
# classes and used twelve of the stylesheet's sixty-seven, which produced a valid
# page that looked nothing like the other four books. Yoram, 2026-08-24: "did you
# check how the other books look like?" I had not.
# book6/index.html's inline landing stylesheet, lifted verbatim so the five
# book landings match. It is not in styles.css; each book carries its own copy.
LANDING_CSS = """
body { font-family: var(--serif); }
  .landing { max-width: 880px; margin: 0 auto; padding: var(--space-8) var(--space-6); }
  .landing-hero { padding: var(--space-7) 0 var(--space-6); border-bottom: 1px solid var(--rule); margin-bottom: var(--space-7); }
  .landing-eyebrow { font-family: var(--sans); font-size: 11px; font-weight: 600; letter-spacing: 0.09em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: var(--space-3); }
  .landing-back { font-family: var(--sans); font-size: 13px; color: var(--ink-muted); margin-bottom: var(--space-4); }
  .landing-back a { color: var(--blue-deep); text-decoration: none; }
  .landing-back a:hover { text-decoration: underline; }
  .landing-title { font-family: var(--serif); font-size: 44px; font-weight: 700; line-height: 1.1; color: var(--ink); margin-bottom: var(--space-3); }
  .landing-subtitle { font-family: var(--serif); font-size: 22px; font-weight: 400; line-height: 1.3; color: var(--ink-soft); margin-bottom: var(--space-4); font-style: italic; }
  .landing-byline { font-family: var(--sans); font-size: 14px; color: var(--ink-muted); }
  .landing-byline a { color: var(--blue-deep); text-decoration: none; }
  .landing-section { margin-bottom: var(--space-7); }
  .landing-section h2 { font-family: var(--serif); font-size: 24px; font-weight: 600; margin-bottom: var(--space-4); color: var(--ink); border: none; padding: 0; }
  .landing-section p { font-size: 18px; line-height: 1.65; color: var(--ink); margin-bottom: var(--space-4); }
  .toc-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: var(--space-3) var(--space-5); margin: var(--space-5) 0; }
  .toc-card { padding: var(--space-3) var(--space-4); border: 0.5px solid var(--rule); border-radius: var(--radius-md); background: var(--bg); }
  .toc-card a { color: var(--ink); text-decoration: none; display: block; }
  .toc-card a:hover { color: var(--blue-deep); }
  .toc-num { font-family: var(--sans); font-size: 11px; font-weight: 500; color: var(--ink-muted); letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 2px; }
  .toc-title { font-family: var(--serif); font-size: 16px; font-weight: 500; line-height: 1.3; }
  .cta-row { display: flex; gap: var(--space-3); flex-wrap: wrap; margin: var(--space-5) 0; }
  .cta-btn { padding: var(--space-3) var(--space-5); font-family: var(--sans); font-size: 14px; font-weight: 500; border-radius: var(--radius-md); text-decoration: none; transition: all 0.15s; border: 1px solid var(--ink); }
  .cta-primary { background: var(--ink); color: var(--bg); }
  .cta-primary:hover { background: var(--ink-soft); }
  .cta-secondary { background: transparent; color: var(--ink); }
  .cta-secondary:hover { background: var(--tint-warm); }
  .landing-footer { margin-top: var(--space-8); padding-top: var(--space-5); border-top: 1px solid var(--rule); font-family: var(--sans); font-size: 13px; color: var(--ink-muted); }
  .landing-footer a { color: var(--blue-deep); text-decoration: none; }
  @media (max-width: 720px) { .toc-grid { grid-template-columns: 1fr; } .landing-title { font-size: 32px; } }
"""

APPARATUS_CSS = """
    .rule-line { border-top: 1.5px solid var(--ink, #1F2937); border-bottom: 1.5px solid var(--ink, #1F2937);
                 padding: var(--space-3, 12px) 0; margin: var(--space-5, 24px) 0; }
    .table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    /* A card's numbered steps ran straight into "Worked:" with no gap, and the
       gloss and phase-rail boxes had nothing under them before the prose
       resumed. Yoram, 2026-08-24. */
    .callout ol, .callout ul { margin-bottom: var(--space-4, 16px); }
    .callout > p { margin-top: var(--space-3, 12px); }
    .card.gloss, .card.phase-rail { margin: var(--space-5, 24px) 0; }
    .card.gloss + p, .card.phase-rail + p, .rule-line + p { margin-top: var(--space-4, 16px); }
    .phase-tree > summary { list-style: none; cursor: pointer; }
    .phase-tree > summary::-webkit-details-marker { display: none; }
    .phase-tree > summary::before { content: "\\25B8"; display: inline-block;
        width: 1em; color: var(--ink-muted, #777); font-size: 10px;
        transition: transform .12s ease; }
    .phase-tree[open] > summary::before { transform: rotate(90deg); }
    /* The sidebar's link styling is scoped to `.sidebar-list a`, and a summary is
       not inside that list, so the phase rows fell through to the browser default
       and rendered blue and underlined while their own children did not. Yoram,
       2026-08-24: "why does it look like blue underline links?" These mirror
       `.sidebar-list a` rather than reinventing it. */
    .phase-tree > summary { margin-bottom: 4px; }
    .phase-tree > summary a { color: var(--ink-soft); text-decoration: none;
        display: inline-block; padding: 4px 8px; border-radius: var(--radius-sm);
        font-size: 13px; }
    .phase-tree > summary a:hover { background: var(--rule-soft); color: var(--ink); }
    .phase-tree > summary a.active { background: var(--ink); color: var(--bg); }
    .phase-sub { margin: .2rem 0 .5rem 1.1rem; }
    .phase-sub li { margin: .1rem 0; }
    .phase-sub a { font-size: 12px; }
    .tree-kind { display: block; font-size: 9px; letter-spacing: .06em;
                 text-transform: uppercase; color: var(--ink-muted, #777); }
    .pager { display: flex; justify-content: space-between; gap: 1rem;
             margin-top: var(--space-6, 32px); padding-top: var(--space-4, 16px);
             border-top: 0.5px solid var(--rule, #d8d8d4);
             font-family: var(--sans); font-size: 13px; }
"""


def shell(title: str, desc: str, fname: str, meta: str, body: str,
          sidebar: str, pager: str) -> str:
    full = f"{title} · {SITE_TITLE}" if title != SITE_TITLE else SITE_TITLE
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{CANON}{fname if fname != 'index.html' else ''}">
<link rel="stylesheet" href="styles.css">
<style>{APPARATUS_CSS}</style>
</head>
<body>
<div class="book">
  <aside class="sidebar">
    <div class="sidebar-hub"><a href="{HUB}">&larr; All Books</a></div>
    <div class="sidebar-brand"><a href="index.html">{html.escape(SITE_TITLE)}</a>
      <div class="sidebar-brand-sub">{html.escape(SITE_SUB)}</div></div>
{sidebar}
  </aside>
  <div class="main">
    <div class="chapter">
      <div class="chapter-meta">{html.escape(meta)}</div>
      <h1>{html.escape(title)}</h1>
{body}
{pager}
    </div>
  </div>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def split_h2(md: str) -> list[tuple[str, str]]:
    parts = re.split(r"^## (?!#)", md, flags=re.M)[1:]
    out = []
    for p in parts:
        head, _, body = p.partition("\n")
        out.append((head.strip(), body))
    return out


def split_h3(md: str) -> list[tuple[str, str]]:
    parts = re.split(r"^### (?!#)", md, flags=re.M)
    lead = parts[0]
    out = []
    for p in parts[1:]:
        head, _, body = p.partition("\n")
        out.append((head.strip(), body))
    return out, lead


def main() -> None:
    if not SOURCE_MD.exists():
        raise SystemExit(f"source manuscript not found: {SOURCE_MD}\n"
                         "This is how build_web_book6.py froze at v1.4 for weeks. "
                         "Fix the path rather than the symptom.")
    md = SOURCE_MD.read_text(encoding="utf-8")
    OUT.mkdir(exist_ok=True)

    src_css = HERE / "book6" / "styles.css"
    if src_css.exists():
        shutil.copy(src_css, OUT / "styles.css")

    pages: list[tuple[int, str, str, str, str]] = []  # (sort, fname, title, group, html)
    unmapped: list[str] = []

    for h2, body in split_h2(md):
        if h2 in SKIP_DIVISIONS:
            continue
        if h2 in CONTAINER_DIVISIONS:
            units, lead = split_h3(body)
            # The lead is the text between "## Part Two" and its first "### Phase".
            # It is not decorative: Part Two's lead carries Phase 1's entire phase
            # map, and the first version of this builder threw it away, losing 124
            # words without failing. That is precisely the bug this builder's
            # docstring claims it prevents. Found 2026-08-24 by counting rendered
            # phase rails and getting nine where the book has ten.
            lead = lead.strip()
            for n_unit, (h3, ubody) in enumerate(units):
                if n_unit == 0 and lead:
                    ubody = lead + "\n\n" + ubody
                if h3 not in SECTION_MAP:
                    unmapped.append(h3)
                    continue
                fname, group, order = SECTION_MAP[h3]
                base = 100 if group == CH else 200
                found: list = []
                pages.append((base + order, fname, h3, group,
                              render_blocks(ubody, found), found))
            continue
        if h2 in DIVISION_PAGES:
            fname, group, order = DIVISION_PAGES[h2]
            base = {"front": 0, BACK: 300}[group]
            found = []
            pages.append((base + order, fname, h2, group,
                          render_blocks(body, found), found))
            continue
        unmapped.append(h2)

    if unmapped:
        raise SystemExit(
            "unmapped sections, refusing to build a partial book:\n  "
            + "\n  ".join(unmapped)
            + "\n\nAdd them to SECTION_MAP or DIVISION_PAGES deliberately.")

    pages.sort()
    order = [(f, t) for _, f, t, _, _, _ in pages]

    GROUP_LABEL = {"front": "Front Matter", CH: "Part One · The argument",
                   PH: "Part Two · The case", BACK: "After"}
    GROUP_META = {"front": "Front matter", CH: "Part One", PH: "Part Two", BACK: "Back matter"}

    def sidebar_for(current: str) -> str:
        """The series sidebar, plus a collapsible tree for Part Two.

        Books 3 to 6 have flat sidebar lists because their chapters have nothing
        under them. Part Two's five phases each carry six to eleven cards and
        exhibits, so a flat list of five understates the book badly and a flat
        list of forty-six would be unusable. <details> gives a tree with no
        JavaScript, keyboard-accessible, and it degrades to an open list if the
        CSS never loads. The phase you are reading is open; the rest are shut.
        Yoram, 2026-08-24: "collapsable tree for each step."
        """
        out = []
        for g in ("front", CH, PH, BACK):
            items = [(f, t2, fd) for _, f, t2, gg, _b, fd in pages if gg == g]
            if not items:
                continue
            out.append(f'    <div class="sidebar-section">{GROUP_LABEL[g]}</div>')
            if g != PH:
                out.append('    <ul class="sidebar-list">')
                for n, (f, t2, _fd) in enumerate(items, 1):
                    label = f"{n}. {t2.split(' · ', 1)[-1]}" if g == CH else t2.split(" · ", 1)[-1]
                    cls = ' class="active"' if f == current else ""
                    out.append(f'      <li><a href="{f}"{cls}>{html.escape(label)}</a></li>')
                out.append("    </ul>")
                continue
            for n, (f, t2, fd) in enumerate(items, 1):
                here = f == current
                label = f"{n}. {t2.split(' · ', 1)[-1]}"
                cls = ' class="active"' if here else ""
                out.append(f'    <details class="phase-tree"{" open" if here else ""}>')
                out.append(f'      <summary><a href="{f}"{cls}>{html.escape(label)}</a></summary>')
                out.append('      <ul class="sidebar-list phase-sub">')
                for kind, name, anchor in fd:
                    out.append(f'        <li><a href="{f}#{anchor}">'
                               f'<span class="tree-kind">{html.escape(kind)}</span>'
                               f'{html.escape(name)}</a></li>')
                out.append("      </ul>")
                out.append("    </details>")
        return "\n".join(out)

    for idx, (_, fname, title, group, body, _found) in enumerate(pages):
        prev = (f'<a href="{order[idx-1][0]}">&larr; {html.escape(order[idx-1][1])}</a>'
                if idx else "<span></span>")
        nxt = (f'<a href="{order[idx+1][0]}">{html.escape(order[idx+1][1])} &rarr;</a>'
               if idx + 1 < len(order) else "<span></span>")
        page = shell(title, f"{title} — {SITE_TITLE}.", fname, GROUP_META[group],
                     body, sidebar_for(fname), f'<nav class="pager">{prev}{nxt}</nav>')
        (OUT / fname).write_text(page, encoding="utf-8")

    # ---------------------------------------------------------------------
    # Landing page. This is a different template from the chapter pages: the
    # series' book landings are `div.landing` with a hero, a CTA row and a grid
    # of chapter cards, and they carry their own inline CSS rather than using
    # styles.css. The first draft of this builder used the sidebar shell here,
    # which was simply the wrong page. Yoram, 2026-08-24: "the index.html will
    # look very different once published (look at the other books)." The CSS
    # below is book6's, lifted verbatim so the five landings match.
    # ---------------------------------------------------------------------
    def toc_cards() -> str:
        cards = []
        n = 0
        for _, f, t2, gg, _b, _fd in pages:
            if gg in (CH, PH):
                n += 1
                num = f"{'Chapter' if gg == CH else 'Phase'} {t2.split(' · ')[0].split()[-1]}"
            else:
                num = {"front": "Front matter", BACK: "After"}[gg]
            title2 = t2.split(" · ", 1)[-1]
            cards.append(f'<div class="toc-card"><a href="{f}">'
                         f'<div class="toc-num">{html.escape(num)}</div>'
                         f'<div class="toc-title">{html.escape(title2)}</div></a></div>')
        return '<div class="toc-grid">' + "".join(cards) + "</div>"

    first_page = pages[0][1]
    landing = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(SITE_TITLE)}</title>
<meta name="description" content="{html.escape(BOOK_DESC)}">
<link rel="canonical" href="{CANON}">
<link rel="stylesheet" href="styles.css">
<style>
{LANDING_CSS}
</style>
</head>
<body>
<div class="landing">
  <div class="landing-hero">
    <div class="landing-back"><a href="{HUB}">&larr; The Agentic AI Series</a></div>
    <div class="landing-eyebrow">Book 5 in the series &nbsp;&middot;&nbsp; Draft</div>
    <h1 class="landing-title">{html.escape(SITE_TITLE)}</h1>
    <p class="landing-subtitle">{html.escape(SITE_SUB)}</p>
    <div class="landing-byline">By <a href="https://www.linkedin.com/in/yoramf/" target="_blank" rel="noopener">Yoram Friedman</a></div>
  </div>
  <div class="landing-section">
    <p>The first four books are built out of documented incidents and cited research. This one is built the other way, around a single company that does not exist: Ostermill Industrial Supply, followed from the sentence that proposed an agent to the year after it launched.</p>
    <p>Part One is the argument in ten chapters. Part Two is the case in five phases, carrying the thirty procedure cards and eleven case-file exhibits the project produced. Where it compresses an argument, the other four are where that argument is made at length and where it can be checked.</p>
    <div class="cta-row">
      <a class="cta-btn cta-primary" href="{first_page}">Start reading &rarr;</a>
      <a class="cta-btn cta-secondary" href="decide.html">Jump to the case &rarr;</a>
    </div>
  </div>
  <div class="landing-section">
    <h2>Contents</h2>
{toc_cards()}
  </div>
  <footer class="landing-footer">
    <a href="{HUB}">All books in the series</a>
  </footer>
</div>
</body>
</html>
"""
    (OUT / "index.html").write_text(landing, encoding="utf-8")

    # ---- assertions: a partial book must not ship quietly --------------------
    built = "".join((OUT / f).read_text(encoding="utf-8") for _, f, _, _, _, _ in pages)
    cards = built.count('<div class="callout-label">Card</div>')
    exhibits = len(re.findall(r'<div class="callout-label">Exhibit [A-K]</div>', built))
    # Count every kind of apparatus, not only the two I first thought of. The
    # cards-and-exhibits pair passed while a phase map was missing, because a
    # phase map is neither.
    glosses = built.count('class="card gloss"')
    rails = built.count('class="card phase-rail"')
    rules = built.count('class="rule-line"')
    problems = []
    for got, want, what in ((cards, 30, "cards"), (exhibits, 11, "exhibits"),
                            (glosses, 11, "glosses"), (rails, 10, "phase maps"),
                            (rules, 15, "Rules")):
        if got != want:
            problems.append(f"expected {want} {what} in the output, found {got}")
    for _, f, t, _, b, _fd in pages:
        if len(b) < 400:
            problems.append(f"page {f} ({t}) is suspiciously short: {len(b)} chars")
    if problems:
        raise SystemExit("build produced a book that does not match the source:\n  "
                         + "\n  ".join(problems))

    print(f"wrote {OUT}")
    print(f"  {len(pages)} content pages plus index.html")
    print(f"  {cards} cards, {exhibits} exhibits")
    print("  nothing committed or pushed; publish deliberately after the final lock")


if __name__ == "__main__":
    main()
