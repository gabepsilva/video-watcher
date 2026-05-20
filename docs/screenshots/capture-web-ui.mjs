/**
 * Capture web console screenshots for README (requires UI + API on localhost).
 * Usage: node docs/screenshots/capture-web-ui.mjs
 */
import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, "web-ui");
const BASE = process.env.VW_UI_URL ?? "http://127.0.0.1:5173";

async function clickNav(page, label) {
  await page.locator(".sidebar .nav__item", { hasText: label }).click();
  await page.waitForTimeout(500);
}

async function shot(page, name) {
  const file = path.join(OUT, `${name}.png`);
  await page.screenshot({ path: file, fullPage: false });
  console.log("wrote", file);
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.setDefaultTimeout(15000);

  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.waitForSelector(".console");

  await shot(page, "new-transcription");

  await clickNav(page, "Jobs");
  await page.waitForSelector(".job-row");
  await shot(page, "jobs");

  await clickNav(page, "Microphone");
  await page.locator("h1.page__title", { hasText: "Microphone" }).waitFor();
  await shot(page, "microphone");

  await clickNav(page, "Diagnostics");
  await page.locator("h1.page__title", { hasText: "Diagnostics" }).waitFor();
  await shot(page, "diagnostics");

  await clickNav(page, "Jobs");
  await page.locator(".job-row").first().click();
  await page.waitForSelector(".artifacts-card, .artifact-panel");
  await page.waitForTimeout(600);
  await shot(page, "job-detail");

  const txtRow = page.locator(".artifact-panel").filter({ hasText: ".txt" }).first();
  if ((await txtRow.count()) > 0) {
    await txtRow.locator(".artifact-row__toggle").click();
    await page.waitForTimeout(1000);
    await shot(page, "job-artifact-editor");
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
