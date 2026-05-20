# E2E doc format (doc-internal)

E2E specs live beside their ADR: **`doc-internal/features/<area>/e2e-<slug>.md`** or **`doc-internal/proposals/<area>/e2e-<slug>.md`**. Slug matches the ADR (`adr-create-collection.md` ↔ `e2e-create-collection.md`).

**Flexibility:** Pick UI-flow sections, matrix-only sections, or ops-style sections based on what is under test. Omit optional blocks (e.g. user story, sequence diagram) when a tight matrix is enough; split or merge tables if it stays readable. Same idea as [ADR-FORMAT.md](./ADR-FORMAT.md) — conventions are defaults, not a rigid template.

## Cross-link (required)

**Option A** (most feature docs):

```md
# {Short feature title}

Related ADR: [{ADR title}](adr-<slug>.md)
```

**Option B** (some backend/ops docs use a bold companion line):

```md
**Companion:** [ADR — {title}](adr-<slug>.md)
```

Add **Tracking:** issue link and **Status** when useful (`IMPLEMENTED`, backlog coverage TBD, etc.).

## Core sections (UI / Playwright style)

Typical order (see `e2e-create-collection.md`, `e2e-list-collections.md`):

1. **`## User story`** — As a … I want … so that …
2. **`## Use case`** (optional) — Actor, goal, preconditions, success outcome
3. **`## Current behavior under test`** — narrative; **`mermaid` sequenceDiagram** when it clarifies FE/BE interaction
4. **`## Automated E2E test cases`** — markdown **table**:

| Column | Content |
|--------|---------|
| **ID** | Stable id: `TC-<AREA>-NNN` (e.g. `TC-COL-001`, `TC-AUTH-001`, `TC-ZIP-001`) |
| **Scenario** | Short description |
| **Preconditions** | Environment, seed data, auth |
| **Expected result** | Observable outcome (include API/status when relevant) |
| **Coverage** | `Automated (path/to/spec.ts)`, `Planned (…)`, `Planned automated`, or **Partial** |

5. **`## Spec reference`** — bullet list of test file paths (`cloud-jpegs3-frontend/e2e/...` or backend test paths)
6. **`## Run only this spec`** — fenced `bash` block: `cd cloud-jpegs3-frontend` + `bunx playwright test e2e/....spec.ts`

### Variations seen in-repo

- **Contract / backlog matrix** — fewer columns (`ID | Scenario | Expected`) when Playwright does not exist yet; call section **Automated E2E test cases (backlog)** (see `e2e-collection-download-zip.md`).
- **`## Manual / stress backlog`** — separate table for load, edge, or flaky scenarios.
- **`## Preconditions`** / **`## Success path`** — numbered steps for long flows (ZIP export, auth).
- **`## Current behavior note:`** / **ADR alignment** — when behavior is mid-migration; point to ADR sections for transport modes, out-of-scope automation (jobs, metrics).

## Backend / integration / operational E2E

When validation is **not** browser-first (see `e2e-photo-processing-queue-pg-notify.md`, `e2e-kubernetes-jpegs3-observability.md`):

- **`## Purpose`** — what end-to-end path is validated (and what is explicitly out of scope).
- **`## Preconditions`** — docker compose, env vars, DB access, log levels.
- **`## User-visible story (indirect)`** — optional bridge from operator/backend proof to user impact.
- **`## Shipped behavior (reference)`** — mermaid diagram.
- **`## Test matrix`** — grouped scenarios (**T1 — …**, **T2 — …**) with tables: `ID | Step | Action | Expected`.
- State **Automation today:** vs manual / future.

## IDs and naming

- Keep **TC-** (or doc-specific prefixes like **T1.1**) consistent within one file.
- File name: **`e2e-<kebab-feature>.md`** aligned with ADR slug and (when possible) the Playwright spec basename.

## Consistency with the ADR

- ADR **Test Coverage Snapshot** / verification bullets should reference this file by repo path.
- When the ADR lists `error.code` values, the E2E table should include rows for error UX or API responses where applicable.
