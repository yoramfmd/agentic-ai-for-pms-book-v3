#!/usr/bin/env python3
"""Build the /whitepapers/ section from the brochure sources.

Reads MANIFEST.json for metadata and <slug>/_b{1,2,3}.html for body copy,
converts the brochure's print classes to the site's design system, and writes
one landing page plus one article page per paper.

    python3 build_web_whitepapers.py [slug ...]      # default: all in manifest
"""
import json, os, re, sys, shutil

SRC   = os.path.dirname(os.path.abspath(__file__))
WORK  = os.path.dirname(SRC)                       # /root/work
OUT   = os.path.join(SRC, 'whitepapers')
SITE  = 'https://agenticaiproductmanagement.com'

MAN   = json.load(open(os.path.join(WORK, 'wpman', 'MANIFEST.json')))
DESC  = json.load(open(os.path.join(WORK, 'wpman', 'card-descriptions.json')))
DIRS  = json.load(open(os.path.join(SRC, 'slug-dirs.json')))
LINKS = json.load(open(os.path.join(SRC, 'source-links.json')))
CSS   = open(os.path.join(SRC, 'wp.css')).read()

HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="{ogtype}">
<meta property="og:site_name" content="The Agentic AI Series">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="{canon}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogtitle}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og}">
{jsonld}
<link rel="stylesheet" href="{css}">
<style>
{style}</style>
</head>
<body>
"""

FOOT = """
<script defer src="https://cloud.umami.is/script.js" data-website-id="6701185a-719e-4b6f-baaf-dcd504ef6b1a"></script>
<script defer src="{assets}/site-extras.js"></script>
</body>
</html>
"""

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

# ── brochure markup -> site markup ────────────────────────────────────────────

def convert(body, slug):
    """Strip the print cover and remap the brochure's classes."""
    # drop the print cover. Its nesting varies by paper, so match to the closing
    # </div> that follows the byline block rather than to whatever comes next.
    body = re.sub(r'^\s*<div class="cover">.*?<div class="foot">.*?</div>\s*</div>', '',
                  body, flags=re.S)
    # figures: <div class="fig">SVG<div class="figcap">..</div></div>
    body = re.sub(r'<div class="fig">(.*?)<div class="figcap">(.*?)</div>\s*</div>',
                  lambda m: '<figure>%s<figcaption>%s</figcaption></figure>'
                            % (m.group(1).strip(), m.group(2).strip()),
                  body, flags=re.S)
    # pull quotes -> blockquote
    body = re.sub(r'<div class="pull">\s*<p>(.*?)</p>\s*</div>',
                  lambda m: '<blockquote><p>%s</p></blockquote>' % m.group(1).strip(),
                  body, flags=re.S)
    # numbered dimension blocks
    # the lookahead must accept ANY following tag. Restricting it to <div/<h/<p made
    # the non-greedy body backtrack and swallow a following <figure> into the block.
    body = re.sub(r'<div class="dim">\s*<div class="lbl">(.*?)</div>(.*?)</div>\s*(?=<|$)',
                  lambda m: '<div class="wp-num"><div class="wp-num-n">%s</div><div>%s</div></div>'
                            % (m.group(1).strip(), m.group(2).strip()),
                  body, flags=re.S)
    # stat blocks: a big number with an explanation beside it
    body = re.sub(r'<div class="stat">\s*<div class="n">(.*?)</div>\s*<div class="t">(.*?)</div>\s*</div>',
                  lambda m: '<div class="wp-stat"><div class="wp-stat-n">%s</div>'
                            '<div class="wp-stat-t">%s</div></div>'
                            % (m.group(1).strip(), m.group(2).strip()),
                  body, flags=re.S)
    # short numeric cells get held on one line; everything else wraps
    body = re.sub(r'<td>(\s*[~$]?[\d][\d.,%x+ $to-]{0,14}\s*)</td>',
                  lambda m: '<td class="wp-n">%s</td>' % m.group(1), body)
    swaps = [
        ('<div class="story">',   '<div class="callout">'),
        ('<div class="box">',     '<div class="callout">'),
        ('<div class="tinted">',  '<div class="callout">'),
        ('<div class="cols">',    '<div class="wp-cols">'),
        ('class="breakable"',     'class="wp-table"'),
        ('<div class="closing">', '<div class="wp-closing">'),
        ('<div class="note">',    '<div class="wp-note">'),
        ('<div class="part">',    '<div class="wp-part">'),
        ('<p class="lede2">',     '<p class="wp-lede">'),
        ('<h2 class="top">',      '<h2>'),
        ('<div class="sect">',    '<div class="wp-sect">'),
    ]
    for a, b in swaps:
        body = body.replace(a, b)
    # <div class="sect"> closers become </section>; count and rebalance at the end
    body = re.sub(r'\s+style="[^"]*"', '', body)
    return body.strip()

# papers whose content is a dated snapshot get a visible stamp. On a PDF the date
# travels with the file; on an indexed page it does not, so say it out loud.
STAMPS = {
    'what-the-platform-gives-you':
        'Capability survey stamped mid-2026. Platform capability moves quarterly and the '
        'gap line closes fastest. Verify any specific claim before repeating it in a '
        'procurement meeting.',
    'what-an-agent-actually-costs':
        'Model prices stamped mid-2026 and already drifting. The ratios the argument rests '
        'on have held across vendors and three years of price movement; the table has not.',
}

def stamp_block(slug):
    t = STAMPS.get(slug)
    return '\n  <div class="wp-stamp">%s</div>\n' % t if t else ''

def sources_block(slug):
    items = LINKS.get(slug, [])
    if not items:
        return ''
    li = '\n'.join('    <li><a href="%s">%s</a>. %s</li>' % (u, esc(t), esc(n))
                   for t, u, n in items)
    return ('\n<div class="wp-src">\n  <div class="wp-src-h">The books behind this paper</div>\n'
            '  <ul>\n%s\n  </ul>\n</div>\n' % li)

# ── pages ─────────────────────────────────────────────────────────────────────

def build_article(w):
    slug, d = w['slug'], DIRS[w['slug']]
    parts = [os.path.join(WORK, d, '_b%d.html' % i) for i in (1, 2, 3)]
    if not os.path.exists(parts[0]):
        parts = [os.path.join(WORK, d, '_body.html')]
    body = ''.join(open(p).read() for p in parts)
    for i in range(1, 7):
        tag = '__FIG%d__' % i
        p = os.path.join(WORK, d, '_fig%d.svg' % i)
        if tag in body:
            body = body.replace(tag, open(p).read().strip())
    body = re.sub(r'<div class="coverimg">.*?</div>', '', body, flags=re.S)
    body = re.sub(r'__[A-Z0-9]+__', '', body)
    body = convert(body, slug)

    canon = '%s/whitepapers/%s.html' % (SITE, slug)
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": w['title'], "description": DESC[slug],
        "author": {"@type": "Person", "name": "Yoram Friedman",
                   "jobTitle": "Physician and enterprise product leader"},
        "isPartOf": {"@type": "CreativeWorkSeries",
                     "name": "Agentic AI for Product Leaders"},
        "url": canon, "inLanguage": "en",
    }, indent=2)

    head = HEAD.format(
        title='%s &mdash; Agentic AI for Product Leaders' % esc(w['title']),
        desc=esc(DESC[slug]), canon=canon, ogtype='article',
        ogtitle=esc(w['title']), site=SITE, og='%s/whitepapers/og/%s.jpg' % (SITE, slug),
        jsonld='<script type="application/ld+json">\n%s\n</script>' % jsonld,
        css='../book3/styles.css', style=CSS)

    # the paper's own "sources and status" note is fine print: it closes the page,
    # after the links box.
    i = body.rfind('<div class="wp-note">')
    body_note = body[i:] if i > -1 else ''
    body_main = body[:i].rstrip() if i > -1 else body

    mb = round(w['bytes'] / 1024)
    figs = w['figures']
    page = head + f"""<div class="wp wp-art">
  <div class="wp-back"><a href="index.html">&larr; All whitepapers</a></div>
  <div class="wp-eyebrow">Whitepaper &middot; {esc(w['question'])}</div>
  <h1 class="wp-h1">{esc(w['title'])}</h1>
  <div class="wp-sub">{esc(w['subtitle'])}</div>
  <div class="wp-art-meta">Yoram Friedman, MD &middot; {w['pages']} pages &middot; {figs} figures</div>
{stamp_block(slug)}
  <div class="wp-dl">
    <img class="wp-dl-thumb" src="covers/{slug}.jpg" width="800" height="588" alt="">
    <a class="wp-dl-btn" href="pdf/{w['pdf']}" download
       data-umami-event="whitepaper-download"
       data-umami-event-paper="{slug}">Download the PDF</a>
    <span class="wp-dl-note">{w['pages']} pages &middot; {mb} KB &middot; formatted for print and for sharing</span>
  </div>

{body_main}
{sources_block(slug)}
{body_note}
</div>
""" + FOOT.format(assets='../assets')
    # guards: nothing structural should end up nested inside a numbered block
    for tag in ('<figure', '<table', '<h2'):
        for m in re.finditer(r'<div class="wp-num">.*?</div>\s*</div>', page, flags=re.S):
            assert tag not in m.group(0), '%s: %s nested inside a wp-num block' % (slug, tag)
    assert not re.search(r'__[A-Z0-9]+__', page), slug
    open(os.path.join(OUT, slug + '.html'), 'w').write(page)
    return page

def build_landing(papers):
    canon = '%s/whitepapers/' % SITE
    desc = ('Eight short whitepapers for product leaders building agentic AI: cost, '
            'readiness, supervision, prototyping, procurement, and the roles that arrive '
            'with the agent. Free to read and download.')
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Whitepapers", "description": desc, "url": canon,
        "author": {"@type": "Person", "name": "Yoram Friedman"},
        "hasPart": [{"@type": "Article", "name": w['title'],
                     "url": '%s/whitepapers/%s.html' % (SITE, w['slug'])}
                    for w in papers],
    }, indent=2)
    head = HEAD.format(
        title='Whitepapers &mdash; Agentic AI for Product Leaders',
        desc=esc(desc), canon=canon, ogtype='website',
        ogtitle='Whitepapers &mdash; Agentic AI for Product Leaders', site=SITE,
        og='%s/assets/og-series-wide.jpg' % SITE,
        jsonld='<script type="application/ld+json">\n%s\n</script>' % jsonld,
        css='../book3/styles.css', style=CSS)

    cards = []
    for w in papers:
        s = w['slug']
        cards.append(f"""    <a class="wp-card" href="{s}.html">
      <div class="wp-cover-wrap"><img class="wp-cover" src="covers/{s}.jpg" width="800" height="588" loading="lazy"
           alt="{esc(w['title'])}. {esc(w['subtitle'])}."></div>
      <div class="wp-card-body">
        <div class="wp-card-q">{esc(w['question'])}</div>
        <div class="wp-card-desc">{esc(DESC[s])}</div>
        <div class="wp-card-meta"><span>{w['pages']} pages</span><span class="wp-card-cta">Read &rarr;</span></div>
      </div>
    </a>""")

    page = head + """<div class="wp">
  <div class="wp-back"><a href="../index.html">&larr; All books</a></div>
  <div class="wp-hero">
    <div class="wp-eyebrow">Whitepapers &nbsp;&middot;&nbsp; Agentic AI for Product Leaders</div>
    <h1 class="wp-h1">Eight papers, one question each</h1>
    <div class="wp-sub">Short, self-contained, and drawn from the four books.</div>
  </div>

  <div class="wp-intro">
    <p>Each of these answers a single question a product manager actually gets asked, in
    eight to fifteen pages. They are drawn from the series but written to stand alone, so
    you can hand one to a room that has not read any of the books.</p>
    <p>They are ordered here the way I would read them, not alphabetically. Start anywhere.
    Every one is free to read on this page and free to download.</p>
  </div>

  <div class="wp-grid">
""" + '\n'.join(cards) + """
  </div>

  <div class="wp-note">
    <p>All eight are free. No email, no form. If one is useful, the four books behind them
    are free to read online as well.</p>
  </div>
</div>
""" + FOOT.format(assets='../assets')
    open(os.path.join(OUT, 'index.html'), 'w').write(page)

def main():
    os.makedirs(os.path.join(OUT, 'pdf'), exist_ok=True)
    order = MAN['reading_order']
    by = {w['slug']: w for w in MAN['whitepapers']}
    papers = [by[s] for s in order]
    want = sys.argv[1:] or order
    # the landing references every cover, so copy them all regardless of `want`
    for sub in ('covers', 'og'):
        d = os.path.join(OUT, sub)
        os.makedirs(d, exist_ok=True)
        for w in papers:
            img = os.path.join(SRC, sub, w['slug'] + '.jpg')
            if os.path.exists(img):
                shutil.copy(img, os.path.join(d, w['slug'] + '.jpg'))
    build_landing(papers)
    for s in want:
        w = by[s]
        build_article(w)
        src = os.path.join(WORK, DIRS[s], w['pdf'])
        if os.path.exists(src):
            shutil.copy(src, os.path.join(OUT, 'pdf', w['pdf']))
        for sub in ('covers', 'og'):
            img = os.path.join(SRC, sub, s + '.jpg')
            if os.path.exists(img):
                os.makedirs(os.path.join(OUT, sub), exist_ok=True)
                shutil.copy(img, os.path.join(OUT, sub, s + '.jpg'))
        print('built', s)

if __name__ == '__main__':
    main()
