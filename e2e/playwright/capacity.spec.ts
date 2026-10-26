/** Solutions Capacity UAT keyed to FR-CAP IDs, restricted gating (CAP-03 / PUR-06), accessibility and 390px. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openPage(page: Page, path: string, role = "gtm_lead") {
  await page.goto(path);
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Solutions Capacity — FR-CAP", () => {
  test.beforeEach(async ({ page }) => openPage(page, "/solutions-capacity"));

  test("FR-CAP-01 architect load calls out over-capacity architects with a status badge", async ({ page }) => {
    const w = page.getByTestId("widget-architect-load");
    await expect(w.getByTestId("architect-load-callout")).toContainText(/over capacity|Priya Moreau/);
    await expect(w.getByTestId("status-badge").first()).toBeVisible();
    await expect(w.getByText("over capacity").first()).toBeVisible();
  });

  test("FR-CAP-01 an architect row opens the drill-down of their open pursuits", async ({ page }) => {
    const w = page.getByTestId("widget-architect-load");
    await w.locator("[data-testid^='architect-RES-']").first().click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("FR-CAP-02 RFP turnaround shows share within SLA by quarter and a data table", async ({ page }) => {
    const w = page.getByTestId("widget-rfp-turnaround");
    await expect(w.getByTestId("rfp-turnaround-value")).toContainText(/\d+(\.\d)?%/);
    await expect(w.getByTestId("status-badge").first()).toBeVisible();
    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /RFP turnaround by quarter/ })).toBeVisible();
  });

  test("FR-CAP-04 quality score compares won and lost", async ({ page }) => {
    const w = page.getByTestId("widget-quality-scores");
    await expect(w.getByTestId("quality-score-value")).toContainText(/won vs .* lost/);
    await expect(w.getByTestId("quality-won")).toBeVisible();
    await expect(w.getByTestId("quality-lost")).toBeVisible();
  });

  test("FR-CAP-03 cost of sale is shown to a restricted persona", async ({ page }) => {
    const w = page.getByTestId("widget-cost-of-sale");
    await expect(w.getByTestId("cost-of-sale-value")).toContainText(/\d+(\.\d+)?%/);
  });

  test("FR-GEN-07 metric info shows CAP ID", async ({ page }) => {
    await page.getByTestId("metric-info-CAP-02").first().click();
    await expect(page.getByTestId("metric-info-content-CAP-02")).toContainText("CAP-02");
  });
});

test.describe("Restricted gating (AC-03)", () => {
  test("solutions_lead sees the module but CAP-03 is absent, not greyed", async ({ page }) => {
    await openPage(page, "/solutions-capacity", "solutions_lead");
    await expect(page.getByTestId("widget-architect-load")).toBeVisible();
    await expect(page.getByTestId("widget-cost-of-sale")).toHaveCount(0);
  });

  test("PUR-06 margin shows for finance and is absent for solutions_lead", async ({ page }) => {
    await openPage(page, "/pursuits", "finance");
    await expect(page.getByTestId("widget-margin").getByTestId("margin-value")).toContainText("pts");
    await openPage(page, "/pursuits", "solutions_lead");
    await expect(page.getByTestId("widget-win-rate")).toBeVisible();
    await expect(page.getByTestId("widget-margin")).toHaveCount(0);
  });

  for (const role of ["client_partner", "alliance_manager", "marketing"]) {
    test(`${role} persona is denied Solutions Capacity`, async ({ page }) => {
      await openPage(page, "/solutions-capacity", role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("capacity-view")).toHaveCount(0);
    });
  }
});

test.describe("Solutions Capacity accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openPage(page, "/solutions-capacity");
    await expect(page.getByTestId("widget-cost-of-sale").getByTestId("cost-of-sale-value")).toBeVisible();
    await expect(page.getByTestId("widget-architect-load").getByTestId("architect-load-callout")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openPage(page, "/solutions-capacity");
    await expect(page.getByTestId("widget-rfp-turnaround")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
