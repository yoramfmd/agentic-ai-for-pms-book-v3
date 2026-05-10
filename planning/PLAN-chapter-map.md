# v3.0 Chapter Map

*Working document for Yoram's review before writing begins. This is the intended end state, not a list of tasks.*

---

## Audience and positioning

The book is for product managers building AI products in regulated, high-consequence enterprise domains. Three running case-study threads, used selectively to fit the argument:

- **Software engineering.** Closest to every PM's daily work. Anthropic 17% RCT, Bastani -17%, Lightrun 43% production-debug rate, the senior-engineer-as-reviewer-bottleneck pattern. Lead anchor for arguments that need to land on a Tuesday morning.
- **Healthcare and clinical AI.** Sharpest evidence base, most rigorous regulation, highest stakes. Lead anchor for irreversibility, accountability, regulatory framing, and the supervision paradox.
- **SAP enterprise.** The reader's operational vocabulary. Procurement agents, supplier risk, customer support, IoT, S/4HANA workflows. Lead anchor for cost modeling, runtime artifacts, organizational governance.

Each chapter picks the thread that fits the argument best. No chapter is single-thread. No thread is decorative.

---

## Title and front matter

**Title:** Agentic AI for Busy Product Managers (carry forward from v2.3).

**Subtitle (approved):** Designing the Agent and the Supervisor.

**Domain:** agenticaiproductmanagement.com.
**Repo:** github.com/yoramfmd/agentic-ai-for-pms-book-v3.

---

## Chapter map

The book stays at 11 numbered chapters plus preface, plus two appendices. No new top-level chapter. The supervision-paradox thread runs through Ch 1, 4, 7, 8, 10 in coordinated additions, not as a standalone chapter.

Key for the table:
- **Preserved:** existing v2.3 content carried forward.
- **Enriched:** existing v2.3 content extended or sharpened with named additions.
- **New:** material not present in v2.3.
- **Frameworks:** number references map to `frameworks.md` (35 frameworks total in the knowledge base).

---

### Preface

Sharpened from v2.3. Adds the v3.0-vs-v2.3 change paragraph and the three-thread audience framing. Sets up frameworks #24 (Two-Channel) and #33 (Supervision Paradox).

### Chapter 1. What You Need to Know About AI Before You Design Anything

v2.3 Chapter 1 retained substantially. Heart transplant opening preserved. Concept boxes converted to colored card components. Four-layer-stack diagram inline. Two new sections: "The Supervision Paradox" (Bainbridge 1983, Anthropic RCT 17% as lead anchor, Bastani PNAS, Lightrun 43%, Klarna preview, Budzyń Lancet Gastro three months, Maguire/Bohbot/Javadi neurobiology, Kosmyna MIT, Shaw-Nave Wharton, EASA SIB 2025-09 as institutional counter-model) and "Observability Literacy for the PM" (traces, spans, OpenTelemetry, platform-emits-PM-composes contract, behavioral vs. infrastructure observability). Frameworks introduced: #1 Iceberg, #11 Four Design Artifacts (preview), #18 AI Spectrum, **#33 Supervision Paradox** (canonical), #28 Four Apprenticeship Conditions (referenced), #10 Abstraction Layer Obsolescence.

### Chapter 2. You Are Not a Bridge Anymore

v2.3 Chapter 2 retained almost intact. Cadence pass to vary "X. Y. Both matter." rhythm. One paragraph at the end of "Two Products, One PM" naming the supervision paradox at the level of role.

### Chapter 3. Not Every Problem Deserves an Agent

v2.3 Chapter 3 retained intact. Klarna case expanded with the supervisor-population angle (forward-pointer to Ch 7). New sidebar on Earned vs. Scheduled Autonomy (#34) using Utah Doctronic case.

### Chapter 4. You Built the Agent. Now Design the Behavior.

The chapter that grows the most. v2.3 retained. Approval moment subsection enriched with deference allocation (#35) and the supervision paradox. **Adversarial by Default expansion (~1,500 words)** anchored on STAC paper (>90% attack success), Stanford/MIT/CMU/Elloe AI 847-deployment audit (95% tool privilege escalation, 770K-agent OpenClaw incident), Anthropic Claude Mythos and Project Glasswing as the "fence and model on the same upgrade cycle" point. **PocketOS / Cursor blast-radius case (~400 words)** as the closing concrete example.

### Chapter 5. AI Evals: What the Checkmarks Actually Prove

v2.3 retained. LLM-as-judge subsection enriched with the bias literature (longer-answer, position, same-family). RAG poisoning paragraph added.

### Chapter 6. You Can't Measure What You Didn't Design

v2.3 retained, expanded for observability literacy. Three new subsections: real-time vs. retrospective observability, multi-agent observability, data observability (freshness, completeness, referential integrity, context availability, knowledge graph mapping accuracy, RAG poisoning).

### Chapter 7. Change Management for Agentic AI

v2.3 retained. Accountability section extended with the structural version from "The Last Generation" (the supervisor cannot meaningfully be accountable in the regulatory sense when they cannot independently reproduce the reasoning under deskilling pressure). **Apprenticeship section rewritten** with framework #28 fully instantiated: Four Apprenticeship Conditions, ACCEPT trial 28.4% to 22.4%, NEJM 2025 deskilling/never-skilling/mis-skilling taxonomy, Anthropic novice study, EASA institutional response.

### Chapter 8. Silent Degradation, What Your Agent Is Doing When You Stop Watching

v2.3 retained. Four vectors become **five**, adding **Security posture decay** as a fifth named vector. "Profession We Trust Less" extended with Bainbridge 1983 framing.

### Chapter 9. From Frameworks to Boundaries

v2.3 retained. When-wrong spec reordered to match Four-Question Pre-Launch Review owners (#31). One paragraph introducing the Michelin Condition (#32).

### Chapter 10. What You Owe the People Your Agent Will Never See

v2.3 retained. New subsection on the regulatory implication of the supervision paradox: Criterion 4 plus deskilling, EU AI Act high-risk classification, why the product needs its own safety architecture independent of regulatory HITL framing.

### Chapter 11. Operating the Loop, A Field Manual

v2.3 retained. Red Flags and Diagnostic Questions sections extended for supervision paradox, security posture, real-time observability, earned-vs-scheduled autonomy. New section: Reading List for the PM.

### Appendix A: What Your Platform Should Give You vs. What You Produce Yourself

v2.3 retained, with security additions: OWASP Top 10 for Agentic Applications, MAESTRO threat model, agent identity (commodity), tool-restriction-by-source policy (derived), agent-specific runtime sandboxing (gap line).

### Appendix B: Glossary

v2.3 retained, expanded by ~25 terms covering supervision paradox, deskilling/mis-skilling/never-skilling, deference allocation, STAC, tool privilege escalation, memory poisoning, RAG poisoning, MAESTRO, OWASP Top 10 for Agentic Applications, blast radius, kill-switch, real-time observability, data observability, behavioral monitoring, LLM-as-judge bias, instrument half-life, decision-trace capture, MedLog, Project Glasswing, fermentation culture.

---

## Length summary

- v2.3 manuscript: ~73,000 words.
- v3.0 projected: ~85,000 words.
- Net addition: ~12,000 words across the seven chapters that change.
- Net change in number of chapters: zero.

---

## What's not in v3.0

Three things deliberately not added: a new top-level Supervision Design chapter (the thread is integrated across Ch 1, 4, 7, 8, 10), a standalone Security chapter (the Adversarial by Default expansion in Ch 4 plus security-posture decay in Ch 8 covers the territory at PM-literacy altitude), and elaborate code blocks (the design system supports `pre/code` styling but the manuscript uses code sparingly).
