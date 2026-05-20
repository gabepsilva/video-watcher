# AGENTS Manifest

## First Step (Required)

- Read all README if available:
  - `README.md`

- Conditional reading:
  - If you have to work on the folder cloud-jpegs3 then read CODING-REACT.md and CODING-CSS.md
  - If you have to work on the folder jpegs3-rs    then read CODING-RUST.md
  - If you have to code a feature or bug fix       then read TDD.md, E2E.md and MICROSERVICE-ARCH.md. This development technique is not negotiable. DO IT!

## Coding style

Code generation should follow this priority order:

1. **Readability for humans** — Prefer clear, linear flow. Avoid deeply nested or convoluted structures when a simpler shape is possible.
2. **Maintainability** — It is fine to add dependencies when they keep the code concise and focused on core behavior (fewer bespoke layers to own).
3. **Small codebase** — Keep source code files lean and free of dead weight. **Never** sacrifice (1) or (2) to shave bytes or line count; this priority is about avoiding real garbage, not about winning minimalism at the cost of clarity or upkeep.
4. **Avoid oversized files** — Keep files under 500 lines; target much smaller when possible. Break code into focused modules when it improves clarity and maintenance.
5. **Use code documentation, like JSDoc and inline comments appropriately** — Add comments where intent is not obvious.
6. **Document implementation decisions in comments** — When a non-obvious trade-off or workaround is chosen, add a brief comment explaining the decision and why it exists.
7. Always follow the Twelve-Factor App principles. We don't want to keep fighting tools after deployment.

1 - One codebase per app
2 - Explicit, locked dependencies (no surprises)
3 - Config (especially secrets) kept out of code
4 - Backing services treated as replaceable resources
5 - Strict separation of build, release, and run
6 - Stateless processes (state lives in services, not memory)
7 - Apps that bind to ports and run themselves
8 - Horizontal scaling via identical processes
9 - Fast startup + graceful shutdown (disposable instances)
10 - Dev/prod parity (same services, same versions)
11 - Logs as streams (stdout to centralized systems)
12 - Admin tasks run in the same environment as the app