---
name: grill-with-docs
description: Interview-first grilling session that challenges your plan against the existing domain model, sharpens terminology, and writes internal documentation as decisions crystallise — a paired ADR and E2E doc under doc-internal (same patterns as the MkDocs internal site). Invoke when the user wants to stress-test a plan against project language and ADRs; default is one-question-at-a-time interview, not silent implementation.
---

<what-to-do>

## Invocation = interview (default)

Whenever this skill applies — including `@`-mentions, slash invokes, or phrasing like “use grill-with-docs” — **the user expects the grill/interview**, not a shortcut to implementation or a large “prep” diff unless they clearly asked for that instead.

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.

</what-to-do>

<supporting-info>

## Domain awareness

During codebase exploration, also read existing internal docs:

- **ADRs:** `doc-internal/features/**/adr-*.md`, `doc-internal/proposals/**/adr-*.md`
- **E2E companions:** same folder, `e2e-*.md` linked from the ADR (and vice versa)

Use [ADR-FORMAT.md](./ADR-FORMAT.md) and [E2E-FORMAT.md](./E2E-FORMAT.md) so new pages match what already ships in this repo. Treat both as **pattern guides**: include or drop sections per topic (no mandatory full outline).

### Where new docs live

| Situation | Folder |
|-----------|--------|
| Shipped or feature-level design tied to the product surface | `doc-internal/features/<domain>/` (e.g. `collections`, `auth`, `navigation`, `account`) |
| Not shipped yet / exploratory | `doc-internal/proposals/<domain>/` |

**Filenames:** `adr-<short-slug>.md` and `e2e-<short-slug>.md` (same slug for the pair). Example: `adr-create-collection.md` + `e2e-create-collection.md`.

**Navigation:** When you add a new pair that should appear on the internal doc site, append entries under the right section in `doc-internal/mkdocs.yml` (mirror neighbouring ADR/E2E lines).

Do **not** treat root `CONTEXT.md` as the primary output of this skill. Canonical decisions, scope tables, and domain language belong in the **ADR** (and user-visible / QA expectations in the **E2E** doc). If the repo already has a root `CONTEXT.md` for a narrow thread, you may cross-link from the ADR; only edit it when the user explicitly asks.

## During the session

### Challenge against documented language

When the user uses a term that conflicts with an existing ADR or E2E doc, call it out immediately. When terminology is fuzzy, propose a **canonical** term and record it in the ADR (Context, Decision, or a short **Domain language** subsection).

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term and align the E2E preconditions and expected results to that vocabulary.

### Discuss concrete scenarios

Stress-test boundaries with scenarios that become **E2E rows** (IDs, preconditions, expected results, coverage column).

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it and fix the doc or flag **Status** / **Current behavior under test** accordingly.

### Update docs as decisions land

Capture decisions **as they happen**, not in a batch at the end:

1. **ADR** — only the sections that clarify this decision (common ones: context, scope, decision, alternatives, consequences, design, errors, test snapshot); link to E2E.
2. **E2E** — only what QA / automation needs (often user story + matrix + run commands; skip prose blocks when a matrix alone is enough).

Create or extend the **pair** together so they stay in sync. The ADR line 3 pattern is: `Related E2E: [Title](e2e-<slug>.md)`. The E2E doc links back: `Related ADR: …` or **Companion:** as in existing files.

### When to add / expand an ADR

Offer or extend an ADR when the same three gates as before apply (hard to reverse, surprising without context, real trade-off). For this repo, **feature work** usually warrants a full ADR+E2E pair even when some gates are soft, because internal docs are the contract for QA and implementation.

### E2E doc shape

Match the feature: **browser Playwright** flows use the table with `TC-…` IDs and `cloud-jpegs3-frontend/e2e/...` references; **backend / integration / operational** validation uses purpose + test matrix sections (see NOTIFY E2E). Details in [E2E-FORMAT.md](./E2E-FORMAT.md).

</supporting-info>
