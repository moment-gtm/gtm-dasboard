/** Offerings UAT keyed to FR-OFF IDs, plus role checks, accessibility and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openOfferings(page: Page, role = "gtm_lead") {
  await page.goto("/offerings");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Offerings — FR-OFF", () => {
  test.beforeEach(async ({ page }) => openOfferings(page));

  test("FR-OFF-01 pipeline and wins by offering shows the offering-led share and a data table", async ({ page }) => {
    const w = page.getByTestId("widget-offering-pipeline");
    await expect(w.getByTestId("offering-led-share")).toContainText(/\d+(\.\d)?% of pipeline and wins is offering-led/);
    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /Pipeline and wins by offering/ })).toBeVisible();
  });

  test("FR-OFF-02 attach rate shows a status badge and the practice split", async ({ page }) => {
    const w = page.getByTestId("widget-attach-rate");
    await expect(w.getByTestId("attach-rate-value")).toContainText(/\d+(\.\d)?%/);
    await expect(w.getByTestId("status-badge").first()).toBeVisible();
    await expect(w.locator("[data-testid^='attach-']").filter({ hasText: "practice" }).first()).toBeVisible();
  });

  test("FR-OFF-03 AI-led validation shows unvalidated TCV and the largest unvalidated deals", async ({ page }) => {
    const w = page.getByTestId("widget-ai-validation");
    await expect(w.getByTestId("unvalidated-value")).toContainText(/\$\d+(\.\d)?M/);
    await expect(w.locator("[data-testid^='validation-']")).toHaveCount(3);
    await expect(w.getByRole("heading", { name: "Largest unvalidated deals" })).toBeVisible();
    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /Largest unvalidated/ })).toBeVisible();
  });

  test("FR-OFF-04 asset reuse lists assets and flags low reuse / refresh due in text", async ({ page }) => {
    const w = page.getByTestId("widget-asset-reuse");
    await expect(w.getByTestId("reuse-summary")).toContainText("uses across");
    await expect(w.getByTestId("asset-register-row").first()).toBeVisible();
    await expect(w.getByText(/Low reuse|Refresh due/).first()).toBeVisible();
  });

  test("FR-OFF-05 assets developed compares released to plan and excludes incomplete records (DQ-09)", async ({ page }) => {
    const w = page.getByTestId("widget-asset-build");
    await expect(w.getByTestId("build-summary")).toContainText(/released vs/);
    await expect(w.getByTestId("reuse-share")).toBeVisible();
    await expect(w.getByTestId("build-incomplete")).toContainText("3 released assets are excluded");
  });

  test("FR-GEN-07 metric info shows OFF ID", async ({ page }) => {
    await page.getByTestId("metric-info-OFF-03").first().click();
    await expect(page.getByTestId("metric-info-content-OFF-03")).toContainText("OFF-03");
  });
});

test.describe("Offerings roles", () => {
  for (const role of ["client_partner", "marketing"]) {
    test(`${role} persona is denied the Offerings module`, async ({ page }) => {
      await openOfferings(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("offerings-view")).toHaveCount(0);
    });
  }

  for (const role of ["alliance_manager", "solutions_lead"]) {
    test(`${role} persona can open Offerings`, async ({ page }) => {
      await openOfferings(page, role);
      await expect(page.getByTestId("widget-attach-rate")).toBeVisible();
    });
  }
});

test.describe("Offerings accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openOfferings(page);
    await expect(page.getByTestId("widget-asset-reuse").getByTestId("reuse-summary")).toBeVisible();
    await expect(page.getByTestId("widget-offering-pipeline").getByTestId("offering-led-share")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openOfferings(page);
    await expect(page.getByTestId("widget-attach-rate")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
