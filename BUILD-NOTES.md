# Build notes

How the generators in this repo find their sources, and what changed on 2026-09-26.

---

## Sources are resolved in one place

Every generator here reads manuscripts that live **outside this repo**, in the iCloud
working folder. None of them may compute that location by walking up from its own
position on disk.

`_bookpaths.py` is the only file that knows where anything is. It checks that a path
exists before returning it, and a wrong path stops the build with a message naming the
missing directory and the variable that overrides it.

    from _bookpaths import book_source, shared_css, skills_source

| Override | Default | What it points at |
|---|---|---|
| `BOOKS_ROOT` | `~/Library/Mobile Documents/com~apple~CloudDocs/ClaudeAI/books` | the manuscript directories |
| `SITE_ROOT` | this repo | the site itself |
| `SKILLS_ROOT` | `~/repos/agentic-ai-pm-skill-package` | the agentic PM skill package |

Audit everything in one command. It exits non-zero if anything is missing:

    python3 _bookpaths.py

Run it first whenever a build behaves oddly, and after anything moves.

### Why the rule exists

Until 2026-09-10 this repo sat inside `ClaudeAI/books/`, so `Path(__file__).parent.parent`
happened to land on the manuscript directories. That was a coincidence, not a path. Moving
the repo to `~/repos/` made one level up resolve to `~/repos`, which holds no manuscripts.

Nothing announced it. `build_web_book5.py` still ran, read an empty chapter list, and failed
much later on a missing stylesheet, so the error named the wrong file entirely. All four book
builders were broken for two days while the site kept serving the last good build.

**Do not reintroduce a relative walk-up, and do not hardcode an account name.**
`/Users/I030696/` survived in two sync scripts for months after a machine migration because
nothing ever failed loudly enough to be noticed.

### Which generators are wired, and when

| Generator | Wired |
|---|---|
| `build_web_book4.py` … `build_web_book7.py` | 2026-09-12 |
| `build_web_skills.py` | **2026-09-26** |
| `gen_backmatter.py` | **2026-09-26** |
| `build_web_whitepapers.py` | reads from inside this repo; no external source |

The last two were missed on the 12th, when the sweep covered only the four book builders.
`build_web_skills.py` was additionally pointing at `ClaudeAI/skills/agentic-pm-skill-package`,
a location retired on 2026-09-10 when that package moved to `~/repos/`.

As of 2026-09-26 the repo contains **zero** occurrences of `HERE.parent` used for a source
path, and zero references to any retired location.

---

## Book subtitles are canon, and they drifted

Corrected 2026-09-26, after two of them were found to be invented.

**The only trustworthy source is the printed title page**, in
`books/_series/as-published/`. Not another web page, not the hub, not a previous build.

| Book | Subtitle |
|---|---|
| Agentic AI for Busy Product Managers | A Practitioner's Guide to the New PM Job |
| Why Agentic AI Products Fail | A Product Manager's Guide to Designing the Supervisory Layer |
| The Agentic AI Team | Who Owns What When the Software Acts on Its Own |
| The Agentic AI Practitioner | Keeping the Judgment the Machine Cannot Hold |

Two were wrong, in three places each. `build_web_book4.py` and `build_web_book5.py` carried
invented strings in `SITE_SUB`, which put them in every page's sidebar, every `<title>`, and
the JSON-LD `alternativeHeadline` that search engines read. The hand-maintained hub
`index.html` carried a **third** variant for Book 2, matching neither.

So that book's subtitle existed in three wordings across the corpus and none was the printed
one. It survived nine cold reads of the OneBook because the page listing them is internally
perfect; nothing in the book contradicts a subtitle, so nothing triggered a check.

**Check a subtitle against the title page, never against another copy of itself.**

---

## Rebuilding after a book rev

The OneBook is locked. Confirm what you are building from before you build:

    cd books/OneBook/proof/pipeline && python3 booklock.py status

**Currently rev 52, `efdf672543fa`, 67,506 words, 250 pages, locked 2026-09-26.**

Then, from this repo:

    python3 _bookpaths.py            # audit first
    python3 build_web_book7.py       # the OneBook

A clean rebuild touches only the pages whose content changed. If it rewrites everything,
either a shared string moved (the subtitle lives in every sidebar, so a `SITE_SUB` change
legitimately rewrites the whole book) or something else did, and it is worth knowing which
before committing.

Nothing here auto-commits. Commit and push deliberately.
