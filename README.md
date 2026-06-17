# The Agentic AI Series — Web Editions

Source for the web editions of *The Agentic AI Series* by Yoram Friedman, published at
[agenticaiproductmanagement.com](https://agenticaiproductmanagement.com/).

Four books, each free to read online, each also available in print on Amazon.

## The series

| # | Title | Subtitle | Folder | Status |
|---|-------|----------|--------|--------|
| 1 | Agentic AI for Busy Product Managers | Designing the Agent and the Supervisor | `book3/` | Published |
| 2 | Why Agentic AI Products Fail | Building the Supervisory Layer That Governs It | `book4/` | Published |
| 3 | The Agentic Team | How Agentic AI Reshapes the Roles That Build It | `book5/` | Draft |
| 4 | The Agentic AI Practitioner | Keeping the Judgment the Machine Cannot Hold | `book6/` | Draft |

The hub page is `index.html` (the landing for the series).
Each `bookN/` folder is a self-contained static site: one HTML page per chapter,
plus a `styles.css`, plus a per-book `index.html` (TOC and book-level landing).

## Repository layout

```
series-web/
├── index.html               hub landing page (links to all four books)
├── build_web_book4.py       build script for Book 2 (Why Agentic AI Products Fail)
├── build_web_book5.py       build script for Book 3 (The Agentic Team)
├── build_web_book6.py       build script for Book 4 (The Agentic AI Practitioner)
├── gen_backmatter.py        helper used by the build scripts
├── book3/                   generated web edition, Book 1
├── book4/                   generated web edition, Book 2
├── book5/                   generated web edition, Book 3
└── book6/                   generated web edition, Book 4
```

Source MD lives one level up (in `../AgenticPMGuide/`, `../AgenticFailure/`, `../AgenticTeam/`,
`../AgenticPractitioner/`). The web build is downstream of the authoritative print build.

## Build commands

Run from this directory (`series-web/`):

```bash
python3 build_web_book4.py     # rebuilds book4/
python3 build_web_book5.py     # rebuilds book5/
python3 build_web_book6.py     # rebuilds book6/
```

Book 3 (book3/) is the original online edition; it is not regenerated from these scripts.

The build scripts share the same engine (markdown to HTML, sidebar, page shell,
landing index). Each book script differs only in: source path, output path, site title,
canonical URL, and the chapter list (or, for book6, the H1 split policy against the
consolidated reading copy).

Dependencies: Python 3.10+ standard library only. No external packages.

## Deployment

GitHub Pages serves directly from this folder. There is no build pipeline outside
the local Python scripts; the static HTML files committed here are what gets served.

## Style and design

- Serif body (Source Serif Pro), sans-serif sidebar and metadata (Inter)
- Two-column layout: sticky sidebar on the left, chapter on the right
- Mobile: sidebar collapses; single-column reading
- Color accents per book: blue (Book 1), violet (Book 2), green (Book 3), orange (Book 4)
- Callouts: generic boxed (white-on-cream), and a "Keep in your pocket" pocket variant

The shared stylesheet lives at `../AgenticPMGuide/Web/docs/styles.css` and is copied
into each `bookN/` folder during build.

## License

All content © 2026 Yoram Friedman. All rights reserved. The build scripts are
provided as-is for reference; the manuscripts they render are not open content.
