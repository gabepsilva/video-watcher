# CDP + Brave — reference

## Useful HTTP endpoints (GET)

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:9222/json/version` | Browser version, `webSocketDebuggerUrl` |
| `http://127.0.0.1:9222/json/list` | Open targets (pages, extensions, etc.) |
| `http://127.0.0.1:9222/json/new?https://example.com` | Open a tab (optional) |

Filter pages: JSON `list` entries where `type` is `page` and `webSocketDebuggerUrl` is present.

## Picking the right tab

After connect, `context.pages[0]` may be an extension or `about:blank`. Safer: match `page.url` to the tab you care about, or open a dedicated tab with `json/new?…` and attach to that target (see HTTP table above). You can also `curl -s http://127.0.0.1:9222/json/list` and choose by `url` / `title`.

## Authenticated vs clean session (CDP)

| Goal | Pattern |
|------|--------|
| Reuse logins in the Brave profile | `browser.contexts[0]`, then pick `context.pages[…]` |
| Isolated session (no cookies from profile) | `browser.new_context()` then `new_page()` — note this is **not** the same cookie jar as the visible default profile |

## Playwright (Python) — attach and extract

Requires: `pip install playwright` then `playwright install chromium` (Playwright uses its own Chromium build only for the **driver**; `connect_over_cdp` talks to **Brave**).

**Fidelity:** Playwright documents that CDP attach is **lower fidelity** than a native Playwright launch for some APIs — if something is unsupported, fall back to raw CDP or a different control path. See [BrowserType](https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp).

```python
import json
import sys
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"
URL = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"

def main():
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        title = page.title()
        print(json.dumps({"title": title, "url": page.url}))

if __name__ == "__main__":
    main()
```

### New tab instead of reusing the first

```python
page = context.new_page()
page.goto("https://…")
```

### Extract via locator

```python
text = page.locator("article").inner_text()
rows = page.locator("table tr").all_inner_texts()
```

### Evaluate in page (complex DOM)

```python
data = page.evaluate("""() => {
  return Array.from(document.querySelectorAll('a[href]'), a => ({
    text: a.innerText.trim(),
    href: a.href
  })).slice(0, 50);
}""")
```

## Playwright (async) sketch

Same idea with `async_playwright()` and `await chromium.connect_over_cdp(CDP)` for concurrent waits.

## Selenium 4 Python attach

Requires: `pip install selenium` and a **ChromeDriver** whose major version matches the Brave/Chromium build (Selenium Manager can resolve it when `chromedriver` is not pinned manually).

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

opts = Options()
opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=opts)
driver.get("https://example.com")
print(driver.title)
driver.quit()  # ends the WebDriver session; Brave is a separate process from `brave-browser --remote-debugging-port=…`
```

If `quit()` unexpectedly closes the last window for your Selenium/ChromeDriver pair, skip it and exit the script after work, or upgrade Selenium Manager / driver to match Brave’s Chromium major version.

Use `debuggerAddress` only after Brave is listening on that port. To drive a **specific** tab, switch window: `driver.switch_to.window(driver.window_handles[i])`.

## Security

Scripts run with the user’s filesystem and cookies for that **user-data-dir**. Do not point at a sensitive profile unless the user explicitly requests it. Prefer `$HOME/chrome-cdp-demo` or another dedicated dir.

Anyone who can reach the debug port (same machine, or mis-bound interfaces) can drive the browser and read session state — treat CDP like **root on that profile**.

## Related patterns people use

- **“CDP pattern”:** one long-lived headed browser + attach for flows where the human logs in once and scripts reuse the session ([example write-up](https://prasitmankad.com/blog/cdp-pattern-automate-any-website/)).
- **Playwright / MCP “attach”:** same idea from IDE tooling — connect to an existing tab instead of cold-launching ([Playwright attach docs](https://playwright.dev/docs/agent-cli/commands/attach)).
- **Selenium 4:** attach with `debuggerAddress` — see [Selenium 4 Python attach](#selenium-4-python-attach) above.

## Troubleshooting

- **Connection refused:** Brave not started with `--remote-debugging-port`, or wrong port.
- **Empty contexts:** rare; `browser.new_context()` then `new_page()`.
- **Target closed:** user closed the tab; list targets again or open `json/new`.
