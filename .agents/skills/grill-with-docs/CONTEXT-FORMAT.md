# Root CONTEXT.md (optional — not default for this skill)

This skill **does not** create or maintain `CONTEXT.md` as the primary artifact. Use a **paired ADR + E2E** under `doc-internal/` per [SKILL.md](./SKILL.md), [ADR-FORMAT.md](./ADR-FORMAT.md), and [E2E-FORMAT.md](./E2E-FORMAT.md).

Use a root **`CONTEXT.md`** only when the user explicitly wants a short-lived glossary for a single thread (e.g. compare-mode vocabulary) **and** asks you to update it. In that case:

- Keep it **narrow** to the thread’s topic; do not duplicate the ADR’s scope table or decision.
- Prefer **`## Language`** entries: term, one-sentence definition, **`_Avoid_:`** aliases.
- **`## Relationships`** / **`## Example dialogue`** / **`## Flagged ambiguities`** are optional, same spirit as before.

For anything that belongs in the product record (scope, APIs, trade-offs, QA matrix), put it in **`doc-internal/.../adr-*.md`** and **`e2e-*.md`** instead.
