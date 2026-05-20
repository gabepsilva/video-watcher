# ADR format (doc-internal)

ADRs in this project live next to their **E2E companion** under `doc-internal/features/<area>/` or `doc-internal/proposals/<area>/`, named **`adr-<slug>.md`**. They follow the same structure as existing internal ADRs (see `doc-internal/features/collections/adr-create-collection.md`, `doc-internal/features/auth/adr-clerk-authentication.md`).

## Shape is request-driven

No fixed outline: **include sections that help this decision**, **drop sections that add noise**, and **add new sections** (same emoji heading style when it fits the repo) when something important does not map to the table below — e.g. rollout plan, SLOs, migration steps, open questions. Reorder subsections inside **Implemented Design** (or the whole doc) when a different flow reads more clearly. The table is a **menu of common patterns**, not a checklist.

## Cross-link (required)

Immediately after the H1 title, link the paired E2E doc (relative path, same directory):

```md
# {Title — often “Feature (Frontend + Backend)” or similar}

Related E2E: [{Short E2E title}](e2e-<same-slug>.md)
```

Use **`Related E2E (future):`** when the E2E is planned but not written yet. Proposal ADRs may use **`Related E2E (API / contract, no gallery UI):`** when the companion is contract-focused.

Optional: link related ADRs (`Related pipeline:`, `../../features/...`).

## Section headings (emoji — match repo convention)

Use when they **earn their place**; skip any that do not apply. Prefer the usual order only when it still reads naturally.

| Section | Purpose |
|---------|---------|
| **## 🚦 Status** | `ACCEPTED`, `IN REVIEW`, `DRAFT`, **shipped vs aspirational**, tracking issue link |
| **## 🧩 Context** | Problem, constraints, prior art, **domain language** if it clarifies the decision |
| **## 🎯 Scope** | Markdown table: **In scope (Yes)** vs **Out of scope (No)** |
| **## ✅ Decision** | What we decided; bullets for rules, limits, API shape |
| **## 🤔 Alternatives considered** | Numbered options; **Rejected** with short rationale |
| **## ⚖️ Consequences** | **Positive** / **Negative or trade-offs** |
| **## 🏗️ Implemented Design** | Subsections: data model/migrations, API/validation, diagrams (`mermaid`), frontend files, layering |
| **## 🧪 Test Coverage Snapshot** | `mermaid` flowchart linking backend / frontend / E2E; bullet pointing at `doc-internal/.../e2e-....md` |
| **## 📘 Error Contract** (if applicable) | JSON shape, `error.code` list with HTTP status |

Additional sections used in larger ADRs: architecture narrative, sequence diagrams, deliverables checklist, observability, security notes — keep the same tone: concrete, testable, linked to code paths.

## Diagrams

Prefer **`mermaid`** (`flowchart`, `sequenceDiagram`, `erDiagram`) inside the ADR; internal MkDocs loads Mermaid.

## Terminology

- Prefer **bold** for domain terms at first precise definition.
- If the grilling session resolves many terms, put them in **Context** or a tight **Domain language** bullet list inside the ADR — do not spin up root `CONTEXT.md` unless the user asks.

## Proposals vs features

- **`doc-internal/proposals/`** — DRAFT / pre-ship; may reference shipped features with relative `../../features/...` links.
- **`doc-internal/features/`** — decisions for shipped or in-flight product surfaces.

## After you add a file

Register the page in **`doc-internal/mkdocs.yml`** under the correct nav group (copy the style of the nearest ADR/E2E pair).
