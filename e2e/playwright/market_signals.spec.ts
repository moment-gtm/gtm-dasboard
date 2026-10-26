/** Market Signals UAT (AC-02) keyed to FR-MKT-01..04, role access (AC-03), accessibility (AC-07), and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openMarketSignals(page: Page, role = "marketing") {
  await page.goto("/market-signals");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Market Signals — FR-MKT", () => {
  test.beforeEach(async ({ page }) => openMarketSignals(page));

  test("FR-MKT-01 thought-leadership output shows POVs published, downloads, engaged visits, and asset register", async ({
    page,
  }) => {
    const w = page.getByTestId("widget-thought-leadership");
    await expect(w).toBeVisible();
    await expect(w.getByTestId("thought-leadership-summary")).toContainText(/POVs published/);
    await expect(w.getByTestId("thought-leadership-summary")).toContainText(/downloads/);
    await expect(w.getByTestId("thought-leadership-summary")).toContainText(/engaged visits/);
    await expect(w.getByTestId("thought-leadership-assets")).toBeVisible();
  });

  test("FR-MKT-02 discovery workshop funnel shows conversion vs 50% goal, status badge, and drills down to opportunities", async ({
    page,
  }) => {
    const w = page.getByTestId("widget-workshop-funnel");
    await expect(w).toBeVisible();
    await expect(w.getByTestId("workshop-funnel-summary")).toContainText(/50(\.0)?% goal/);
    await expect(w.getByTestId("status-badge").first()).toBeVisible();
    await w.getByTestId("funnel-stage-created").click();
    const panel = page.getByTestId("drilldown-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("drilldown-register-row").first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("FR-MKT-03 campaign-sourced pipeline shows CRM <-> SRC-10 reconciliation badge and drills down by campaign", async ({
    page,
  }) => {
    const w = page.getByTestId("widget-campaign-pipeline");
    await expect(w).toBeVisible();
    await expect(w.getByTestId("campaign-reconciliation-badge")).toContainText(/Reconciled/);
    await expect(w.getByTestId("campaign-table")).toBeVisible();
    await w.locator("[data-testid^='campaign-drill-']").first().click();
    const panel = page.getByTestId("drilldown-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("drilldown-register-row").first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("FR-MKT-04 analyst positioning displays prior placement, current placement, and explicit text+icon movement", async ({
    page,
  }) => {
    const w = page.getByTestId("widget-analyst-positioning");
    await expect(w).toBeVisible();
    await expect(w.getByTestId("analyst-positioning-summary")).toContainText(/Leader placements/);
    await expect(w.getByTestId("analyst-positioning-table")).toContainText("Forrester");
    await expect(w.getByTestId("analyst-positioning-table")).toContainText("Gartner");
    const badge = w.locator("[data-testid^='analyst-direction-']").first();
    await expect(badge).toContainText(/Improved|Unchanged|Declined/);
  });

  test("FR-GEN-07 metric info popover shows MKT-03 definition and sources", async ({ page }) => {
    await page.getByTestId("metric-info-MKT-03").first().click();
    const pop = page.getByTestId("metric-info-content-MKT-03");
    await expect(pop).toContainText("MKT-03");
    await expect(pop).toContainText("SRC-01");
    await expect(pop).toContainText("SRC-10");
  });
});

test.describe("Market Signals role access (AC-03)", () => {
  // Access matrix: Shared Architecture doc §5 + Market Signals plan (Finance yes; Alliance no).
  for (const role of ["gtm_lead", "leadership", "finance", "practice_lead", "marketing", "sales_ops"]) {
    test(`${role} can open Market Signals`, async ({ page }) => {
      await openMarketSignals(page, role);
      await expect(page.getByTestId("market-signals-view")).toBeVisible();
    });
  }

  for (const role of ["client_partner", "solutions_lead", "alliance_manager"]) {
    test(`${role} is denied Market Signals`, async ({ page }) => {
      await openMarketSignals(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("market-signals-view")).toHaveCount(0);
    });
  }
});

test.describe("Market Signals accessibility & responsiveness", () => {
  test("AC-07 axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openMarketSignals(page);
    await expect(page.getByTestId("widget-thought-leadership")).toBeVisible();
    await expect(page.getByTestId("widget-analyst-positioning")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("NFR-09 usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openMarketSignals(page);
    await expect(page.getByTestId("widget-thought-leadership")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
