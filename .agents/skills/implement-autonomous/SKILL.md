---
name: implement-autonomous
description: Autonomous feature implementation using gh and kubectl to investigate (including BSQL or read-only exec into DB containers when schema/state matters), git worktrees for isolated edits—**create a linked worktree automatically when the session is not already in one** (never strand work on the principal clone by default), sensible defaults without blocking questions, local plus PR-preview validation, iterative test-fix until verified, and safety rails on kubectl/gh/git. Use when the user asks to implement a feature, ship end-to-end, build with tests, or wants the agent to drive the full loop without hand-holding.
---

# Implement (autonomous)

Execute implementation requests **resourcefully and independently**. Prefer doing over asking.

## Defaults

- **Worktree (not in-place checkout)** — required for implementation work; do **not** switch the user’s principal clone to a feature branch for this flow.
  - **Detect**: From the repo root, compare absolute paths: `git rev-parse --path-format=absolute --git-dir` vs `git rev-parse --path-format=absolute --git-common-dir`. If they are **equal**, the checkout is the **principal** worktree (typical single-clone layout) → you are **not** in a linked worktree yet.
  - **If not in a linked worktree**: **Create one first** before editing: e.g. `git worktree add -b <feature-branch> <new-path> <base>` where `<base>` is `master` (or the issue’s stated base) and `<new-path>` is a sibling directory or another explicit path (avoid colliding with existing worktrees—`git worktree list` helps). `cd` into that new path; all commits and pushes for the task happen there.
  - **If already in a linked worktree** (`git-dir` ≠ `git-common-dir`): keep working in that checkout unless it’s the wrong branch/repo; do not add a second worktree unnecessarily.
  - Push that branch for the PR from the worktree path. Remove when done: `git worktree remove <path>` from the **main** repo (after merge or if abandoning—do not delete with `rm -rf` alone while registered).
- **PR base**: Open PRs against `master` unless the repo or user specifies otherwise.
- **Preview**: PRs from this repo (not forks) that touch preview paths trigger unified preview deploy; read `.github/workflows/preview-pr.yml` and `doc-external/infra/manifests/preview/README.md` (repo root). Preview hosts follow `pr<N>-*.i.jpegs3.com` (docs, internal docs, backend, frontend, MinIO in namespace `jpegs3-pr-<N>`).
- **Investigation**: Use `gh` (issues, PRs, runs, workflow view, API) and read workflows under `.github/workflows/`. Use `kubectl` for read-only inspection by default—see **Safety rails** below.
- **Database**: When state or schema is unclear, inspect the DB directly: use **psql** (read-only queries) if available, or **enter the database container** (e.g. `docker compose exec` on the local stack, or `kubectl exec` into the DB workload in a **preview** namespace) and run the project’s usual SQL client (`psql`, `mysql`, etc.). Prefer preview/local; avoid production unless the user scoped the task there.
- **Assumptions**: When something is ambiguous, pick the most common choice (match nearby code, ADRs, `CONTEXT.md`), note it in the final report, and continue. **Do not** stop for clarifications unless progress is impossible without missing secrets, irreversible prod risk, or a policy the user must decide.

## When to stop and ask

Only for **major blockers**: missing auth to required systems, destructive production impact without a safe path, legal/compliance ambiguity, or contradictory requirements that cannot be reconciled by reasonable defaults. Otherwise unblock yourself (docs, code search, `gh`, cluster inspection, smaller scope).

## Safety rails

Stay autonomous without expanding blast radius. For destructive shell/git/kubectl, follow the user’s careful-mode tooling when present (e.g. gstack `/careful`).

- **Kubernetes**: Treat the cluster as **read-only** unless the user explicitly asked for operational changes. Allowed without extra confirmation: `kubectl get`, `describe`, `logs` (tail reasonable size), `explain`, `api-resources`. Prefer **preview namespaces** (`jpegs3-pr-<N>` and related preview resources). **Exception for this skill**: `kubectl exec` (and similar) is allowed **only** for **read-only database inspection**—connect to the DB pod/container, run non-destructive SQL or shell the client needs, then exit—still prefer preview namespaces; treat production like the rest of this section unless the user explicitly scoped work there. Do **not** run `apply`, `delete`, `patch`, `rollout`, `scale`, `create`, `attach`, `cp`, `replace`, `run`, `debug`, or other mutating verbs unless the user clearly requested that work—and never against unnamed “prod” namespaces for operational changes. Short-lived `port-forward` only for local smoke against preview when needed; tear it down after. If context could be production, verify namespace and intent before any exception.
- **`gh`**: Routine: view issues/PRs, comments that add technical detail, `pr create` / push / `pr view`, `run list` / `run watch` / logs. Do **not** merge PRs, enable auto-merge, edit branch protection, change repo settings, dispatch arbitrary workflows, delete releases, or bulk-close/reopen issues unless the user explicitly asked for that action.
- **Git**: No `git push --force` (or `--force-with-lease`) to shared integration branches (`master`, default remote branches, or branches others use). No rewriting `master` / history there. Prefer descriptive feature branch names to avoid collisions. Use `git worktree remove`, not bare `rm -rf`, on registered worktrees.
- **Secrets**: Never commit secrets, tokens, or real production credentials. Use existing env templates, secret managers, and placeholder patterns. If the fix truly requires a secret you cannot obtain safely, stop and say what is missing.

## Testing loop

1. **Local**: From the feature worktree, run project checks the repo already defines (unit/integration, `cargo test`, `npm test`, linters, `docker compose`, etc.)—follow existing scripts and `AGENTS.md`.
2. **Automated CI**: From the worktree, push the feature branch and open/update a PR; watch workflow runs (`gh run list`, `gh run watch`).
3. **Preview**: After preview deploy succeeds, smoke-test the preview URLs for the PR (or read-only `kubectl` in `jpegs3-pr-<N>`). Add or extend tests so the change stays covered; iterate until checks and your validation pass.

## Close-out report

Summarize: worktree path and branch name, what changed (files/areas), how it was validated (commands, PR link, preview or cluster checks), assumptions made, risks or follow-ups, and anything the user should know before merge.
