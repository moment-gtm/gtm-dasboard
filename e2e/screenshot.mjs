// Capture all 9 module screenshots (desktop 1440px + mobile 390px) for visual review / docs.
// Usage: node screenshot.mjs [outDir]   (servers must be running)
import { chromium } from "@playwright/test";

const out = process.argv[2] ?? "screenshots";
const base = process.env.E2E_BASE_URL ?? "http://localhost:5173";
const MODULES = [
  ["executive", "/executive", "executive-view"],
  ["pipeline", "/pipeline", "pipeline-view"],
  ["pursuits", "/pursuits", "pursuits-view"],
  ["offerings", "/offerings", "offerings-view"],
  ["accounts", "/accounts", "accounts-view"],
  ["partners", "/partners", "partners-view"],
  ["capacity", "/solutions-capacity", "capacity-view"],
  ["market", "/market-signals", "market-signals-view"],
  ["admin", "/admin", "admin-view"],
];

const browser = await chromium.launch();
for (const [slug, route, testId] of MODULES) {
  for (const [suffix, viewport] of [
    ["desktop", { width: 1440, height: 900 }],
    ["390", { width: 390, height: 844 }],
  ]) {
    const page = await browser.newPage({ viewport });
    await page.goto(`${base}${route}`);
    await page.getByTestId(testId).waitFor();
    await page.waitForTimeout(800);
    await page.screenshot({ path: `${out}/${slug}-${suffix}.png`, fullPage: true });
    await page.close();
  }
}
await browser.close();
