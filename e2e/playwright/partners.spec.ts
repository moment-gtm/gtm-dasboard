/** Partners UAT keyed to FR-PAR IDs, plus role/RLS checks, accessibility and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openPartners(page: Page, role = "gtm_lead") {
  await page.goto("/partners");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Partners — FR-PAR", () => {
  test.beforeEach(async ({ page }) => openPartners(page));

  test("FR-PAR-01 pipeline by partner shows sourced and influenced values with a data table", async ({ page }) => {
    const w = page.getByTestId("widget-partner-pipeline");
    await expect(w.getByTestId("partner-pipeline-total")).toContainText(/\$\d+(\.\d)?M\s+open partner pipeline/);
    await w.getByText("Show data table").click();
    const t = w.getByRole("table", { name: /Open partner pipeline/ });
    await expect(t).toBeVisible();
    await expect(t.getByText("Adobe")).toBeVisible();
  });

  test("FR-PAR-02 co-sell compares win rate with and without a partner", async ({ page }) => {
    const w = page.getByTestId("widget-co-sell");
    await expect(w.getByTestId("co-sell-summary")).toContainText(/win rate with a partner/);
    await expect(w.getByTestId("cosell-with_partner")).toBeVisible();
    await expect(w.getByTestId("cosell-without_partner")).toBeVisible();
  });

  test("FR-PAR-03 certifications show certified vs required per partner with status", async ({ page }) => {
    const w = page.getByTestId("widget-certifications");
    await expect(w.getByTestId("cert-summary")).toContainText(/\d+ of \d+ required certifications held/);
    await expect(w.getByTestId("cert-Adobe")).toContainText("23 of 24 certified");
    await expect(w.getByTestId("cert-Adobe").getByTestId("status-badge")).toBeVisible();
    await expect(w.locator("[data-testid^='cert-']").filter({ hasText: "certified" })).toHaveCount(4);
  });

  test("FR-GEN-07 metric info shows PAR ID", async ({ page }) => {
    await page.getByTestId("metric-info-PAR-03").first().click();
    await expect(page.getByTestId("metric-info-content-PAR-03")).toContainText("PAR-03");
  });
});

test.describe("Partners roles & RLS", () => {
  for (const role of ["solutions_lead", "marketing"]) {
    test(`${role} persona is denied the Partners module`, async ({ page }) => {
      await openPartners(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("partners-view")).toHaveCount(0);
    });
  }

  test("alliance manager sees only their own partner's certifications", async ({ page }) => {
    await openPartners(page, "alliance_manager");
    const w = page.getByTestId("widget-certifications");
    await expect(w.getByTestId("cert-Adobe")).toBeVisible();
    await expect(w.getByTestId("cert-Salesforce")).toHaveCount(0);
  });
});

test.describe("Partners accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openPartners(page);
    await expect(page.getByTestId("cert-summary")).toBeVisible();
    await expect(page.getByTestId("co-sell-summary")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openPartners(page);
    await expect(page.getByTestId("widget-partner-pipeline")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
