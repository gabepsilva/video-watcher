---
name: cdp-brave-headed
description: Navigate and extract from the live web using Brave over Chrome DevTools Protocol in headed mode (reuse or launch a debugging instance). Use when the user asks for CDP, headed automation, Brave remote debugging, connect_over_cdp, avoiding headless bot blocks, or Python/Playwright against a real browser profile.
---

# CDP + Brave (headed)

Headless automation often trips **anti-bot** defenses. **Headed Brave with a persistent user-data-dir** behaves like a normal session. The agent connects over **CDP** (same protocol as Chrome) instead of launching a disposable headless browser.

## Decision

1. Prefer **attach to an existing** Brave CDP endpoint when it responds.
2. If nothing is listening on the port, **start Brave** with remote debugging, then attach.
3. Use **short Python + Playwright** scripts for navigation and extraction when the chat session cannot drive CDP directly; keep scripts in-repo or a scratch path the user names.

## Reuse vs start

**Default port:** `9222`. **Default user data dir:** `$HOME/chrome-cdp-demo` (isolated profile; change if the user specifies another).

1. Check CDP is up (HTTP, not WebSocket):

   `curl -sf http://127.0.0.1:9222/json/version >/dev/null && echo OK || echo DOWN`

2. If **DOWN**, start Brave (blocking; user may already run this in another terminal). **Do not** launch a second process with the same `--user-data-dir` while that profile is in use (Chromium locks the directory).

   `brave-browser --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-cdp-demo"`

   Optional hardening: append `--remote-debugging-address=127.0.0.1` so the debug port stays on loopback (defaults are often already local; avoid `0.0.0.0` on untrusted networks — CDP has **no auth**).

   On some Linux installs the binary is `brave` instead of `brave-browser`; use whichever exists on `PATH`.

3. If **OK**, connect with Playwright `connect_over_cdp` to `http://127.0.0.1:9222` (see [REFERENCE.md](REFERENCE.md)).

## Agent workflow (navigation + extraction)

1. **Clarify target:** URL, what to extract (text, attribute, table rows, network response shape), and any login state (reuse profile dir vs fresh).
2. **Ensure endpoint:** curl check → start Brave only if needed.
3. **Pick context / tab:** On CDP attach, **`browser.contexts[0]`** is usually the live profile (cookies, logins). **`browser.new_context()`** is a fresh, typically **unauthenticated** context — use only when you want isolation, not when reusing a logged-in session.
4. **Navigate:** `goto` with realistic `wait_until` (`domcontentloaded` or `networkidle` as appropriate).
5. **Extract:** prefer stable selectors the user names; fall back to role/text locators; for bulk data, evaluate in page or intercept responses (REFERENCE).
6. **Leave browser running** unless the user asked to close it; do not kill their daily driver profile.

## When to add a script

Add a small **Python + Playwright** file when: repeated steps, parsing many nodes, saving artifacts to disk, or assertions must run outside the agent loop. Reuse one pattern: connect → one context → pick page → act → print JSON lines to stdout for the agent to read.

## Pitfalls

- Do **not** use Playwright’s bundled Chromium in **headless** mode for sites that block bots; that misses the point of this skill.
- **Separate user-data-dir** avoids clobbering the user’s main Brave profile, keeps sessions reproducible, and matches current Chromium guidance: remote debugging is meant for **non-default** profiles (see [Chrome remote debugging / user data](https://developer.chrome.com/blog/remote-debugging-port)).
- **CDP is still automation:** some stacks fingerprint DevTools/automation signals. Headed + persistent profile reduces friction; it is not a guarantee against every vendor.
- CDP **WebSocket** URL appears in `/json/version`; Playwright accepts the **HTTP** root for `connect_over_cdp`.
- If port is in use but not Brave, confirm with `/json/version` (`Browser` / `User-Agent` fields).

Extended snippets, tab listing, and extraction examples: [REFERENCE.md](REFERENCE.md).
