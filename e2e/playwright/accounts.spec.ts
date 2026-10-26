/** Accounts UAT keyed to FR-ACC IDs, plus role/RLS checks, accessibility and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openAccounts(page: Page, role = "gtm_lead") {
  await page.goto("/accounts");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Accounts — FR-ACC", () => {
  test.beforeEach(async ({ page }) => openAccounts(page));

  test("FR-ACC-01 penetration matrix shows every practice with text-labelled cells", async ({ page }) => {
    const w = page.getByTestId("widget-penetration");
    await expect(w.getByTestId("penetration-summary")).toContainText(/\d+(\.\d)?% of \d+ accounts/);
    const m = w.getByTestId("penetration-matrix");
    await expect(m.getByRole("columnheader")).toHaveCount(9);
    await expect(m.getByRole("img", { name: /: Sold$/ }).first()).toBeVisible();
    await expect(m.getByRole("img", { name: /: Open$/ }).first()).toBeVisible();
  });

  test("FR-ACC-02 whitespace summary shows a status and a row per practice", async ({ page }) => {
    const w = page.getByTestId("widget-whitespace");
    await expect(w.getByTestId("whitespace-summary")).toContainText("whitespace pairs are pursued");
    await expect(w.getByTestId("status-badge").first()).toBeVisible();
    await expect(w.locator("[data-testid^='whitespace-']").filter({ hasText: "Strategy" })).toBeVisible();
  });

  test("FR-ACC-03 expansion vs new logo shows both shares", async ({ page }) => {
    const w = page.getByTestId("widget-expansion");
    await expect(w.getByTestId("expansion-summary")).toContainText("of won TCV is expansion");
    await expect(w.getByTestId("expansion-expansion")).toBeVisible();
    await expect(w.getByTestId("expansion-new_logo")).toBeVisible();
  });

  test("FR-ACC-04 plan health lists strategic accounts with text health labels", async ({ page }) => {
    const w = page.getByTestId("widget-plan-health");
    await expect(w.getByTestId("plan-health-summary")).toContainText("strategic plans are current");
    await expect(w.getByTestId("plan-health-register-row").first()).toBeVisible();
    await expect(w.getByText(/Needs update|Overdue|Current/).first()).toBeVisible();
  });

  test("FR-ACC-05 account detail opens from the matrix, lists opportunities, traps focus and closes on Esc", async ({ page }) => {
    const first = page.getByTestId("penetration-matrix").getByRole("button").first();
    await first.click();
    const panel = page.getByTestId("account-detail-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("account-detail-register-row").first()).toBeVisible();
    await page.keyboard.press("Tab");
    expect(await panel.evaluate((el) => el.contains(document.activeElement))).toBe(true);
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });
});

test.describe("Accounts roles & RLS", () => {
  for (const role of ["solutions_lead", "alliance_manager", "marketing"]) {
    test(`${role} persona is denied the Accounts module`, async ({ page }) => {
      await openAccounts(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("accounts-view")).toHaveCount(0);
    });
  }

  test("client partner sees fewer accounts than the GTM lead", async ({ page }) => {
    const count = async () => {
      const txt = await page.getByTestId("penetration-summary").innerText();
      return Number(/of (\d+) accounts/.exec(txt)![1]);
    };
    await openAccounts(page);
    const all = await count();
    await openAccounts(page, "client_partner");
    await expect(page.getByTestId("accounts-view")).toBeVisible();
    expect(await count()).toBeLessThan(all);
  });
});

test.describe("Accounts accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openAccounts(page);
    await expect(page.getByTestId("penetration-summary")).toBeVisible();
    await expect(page.getByTestId("plan-health-summary")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAccounts(page);
    await expect(page.getByTestId("widget-penetration")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
