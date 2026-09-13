#!/usr/bin/env python3
"""Where the book sources live, resolved in one place.

Why this file exists
--------------------
Until 2026-09-10 this repository sat inside iCloud Drive at
``ClaudeAI/books/agentic-ai-for-pms-book-v3``. Every builder therefore reached its
sources with ``Path(__file__).parent.parent / "AgenticTeam"``, because one level up
was ``ClaudeAI/books/``, which held all the manuscript directories.

iCloud evicts cold files, and it does not know that a blob under ``.git/objects`` is
load-bearing, so the repository was moved to ``~/repos/``. That silently broke every
builder: one level up is now ``~/repos``, which contains no manuscripts. The failure
was not loud. ``build_web_book5.py`` ran, found nothing, and only stopped later on a
missing stylesheet, which is the worst kind of breakage because the error names the
wrong thing.

The rule going forward: no builder computes a source path by walking up from its own
location. Sources are resolved here, the answer is checked, and a wrong answer stops
the build with a message that names the missing directory and the variable that
overrides it.

If the folders move again, change the two defaults below and nothing else.

Usage
-----
    from _bookpaths import BOOKS, SITE, book_source, shared_css

    CHAPTERS = book_source("AgenticTeam", "chapters")
    src_css  = shared_css()

Environment overrides, useful when running somewhere the defaults do not apply, such
as a Linux sandbox that mounts the folders at different paths:

    BOOKS_ROOT   path to the directory holding AgenticTeam, AgenticFailure, OneBook, ...
    SITE_ROOT    path to this repository, normally its own location
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Default for a Mac with the working folder in iCloud Drive. The manuscripts stay in
# iCloud deliberately; only the git repositories were moved out, because the eviction
# problem is specific to git object storage.
_DEFAULT_BOOKS = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/ClaudeAI/books"

BOOKS = Path(os.environ.get("BOOKS_ROOT") or _DEFAULT_BOOKS).expanduser()
SITE = Path(os.environ.get("SITE_ROOT") or Path(__file__).resolve().parent).expanduser()


def _fail(what: str, path: Path, var: str) -> None:
    sys.exit(
        "\n".join(
            [
                "",
                "BUILD STOPPED: %s not found." % what,
                "  looked in: %s" % path,
                "",
                "  This usually means a folder moved. Set %s to the correct location," % var,
                "  or edit the default in _bookpaths.py, which is the single place that",
                "  knows where the sources live.",
                "",
                "  Current settings:",
                "    BOOKS_ROOT = %s" % BOOKS,
                "    SITE_ROOT  = %s" % SITE,
                "",
            ]
        )
    )


def book_source(*parts: str) -> Path:
    """Resolve a path under the books root and refuse to return one that is absent."""
    p = BOOKS.joinpath(*parts)
    if not p.exists():
        _fail("book source %s" % "/".join(parts), p, "BOOKS_ROOT")
    return p


def shared_css() -> Path:
    """The stylesheet every book web edition copies into its output directory."""
    return book_source("AgenticPMGuide", "Web", "docs", "styles.css")


def check() -> None:
    """Verify every path the builders depend on. Run directly to audit the setup."""
    if not BOOKS.exists():
        _fail("books root", BOOKS, "BOOKS_ROOT")
    targets = [
        ("book 2 manuscript", ("AgenticFailure", "MANUSCRIPT-v4.0-FULL-current-2026-05-31.md")),
        ("book 3 chapters", ("AgenticTeam", "chapters")),
        ("book 4 manuscript", ("AgenticPractitioner", "BOOK4-FULL-DRAFT-v1.8-READING-COPY.md")),
        ("book 5 manuscript", ("OneBook", "AGENTIC-AI-FOR-PRODUCT-LEADERS.md")),
        ("shared stylesheet", ("AgenticPMGuide", "Web", "docs", "styles.css")),
    ]
    print("BOOKS_ROOT = %s" % BOOKS)
    print("SITE_ROOT  = %s" % SITE)
    print("")
    bad = 0
    for label, parts in targets:
        p = BOOKS.joinpath(*parts)
        ok = p.exists()
        bad += 0 if ok else 1
        print("  %-20s %s  %s" % (label, "ok     " if ok else "MISSING", p))
    print("")
    print("%d of %d present." % (len(targets) - bad, len(targets)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    check()
