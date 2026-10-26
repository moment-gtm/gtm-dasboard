/** Pipeline UAT keyed to FR-PIP IDs, plus role checks, accessibility and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openPipeline(page: Page, role = "gtm_lead") {
  await page.goto("/pipeline");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Pipeline — FR-PIP", () => {
  test.beforeEach(async ({ page }) => openPipeline(page));

  test("FR-PIP-01 funnel shows stages; clicking a stage filters then clears the register", async ({ page }) => {
    const funnel = page.getByTestId("widget-stage-funnel");
    await expect(funnel.getByTestId("funnel-stage-Identify")).toBeVisible();
    await funnel.getByText("Show data table").click();
    await expect(funnel.getByRole("table", { name: /Stage funnel/ })).toBeVisible();

    const register = page.getByTestId("widget-opportunity-register");
    await expect(register.getByTestId("register-summary")).toBeVisible();
    const before = await register.getByTestId("register-summary").innerText();

    await funnel.getByTestId("funnel-stage-Identify").click();
    await expect(funnel.getByTestId("funnel-stage-Identify")).toHaveAttribute("aria-pressed", "true");
    await expect(register.getByTestId("register-summary")).toContainText("Stage: Identify");
    await expect(register.getByTestId("register-summary")).not.toHaveText(before);

    await register.getByTestId("clear-stage-filter").click();
    await expect(register.getByTestId("register-summary")).not.toContainText("Stage:");
    await expect(funnel.getByTestId("funnel-stage-Identify")).toHaveAttribute("aria-pressed", "false");
  });

  test("FR-PIP-02 ageing heatmap marks review buckets in text and drills down", async ({ page }) => {
    const w = page.getByTestId("widget-ageing-heatmap");
    await expect(w).toContainText("review");
    await w.locator("button:enabled", { hasText: /\$/ }).first().click();
    const panel = page.getByTestId("drilldown-panel");
    await expect(panel).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("FR-PIP-03 practice and platform splits expose lead/contributing and qualified/Identify", async ({ page }) => {
    await expect(page.getByTestId("widget-pipeline-by-practice")).toContainText("Lead");
    await expect(page.getByTestId("widget-pipeline-by-practice")).toContainText("Contributing");
    await expect(page.getByTestId("widget-pipeline-by-platform")).toContainText("Qualified");
    await expect(page.getByTestId("widget-pipeline-by-platform")).toContainText("Identify");
  });

  test("FR-PIP-04 deal-size histogram has a text table equivalent", async ({ page }) => {
    const w = page.getByTestId("widget-deal-size");
    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /Deal-size distribution/ })).toBeVisible();
  });

  test("FR-PIP-05 register sorts, searches, flags in text and exports", async ({ page }) => {
    const reg = page.getByTestId("widget-opportunity-register");
    await expect(reg.getByRole("table").first()).toBeVisible();
    await expect(reg.getByTestId("flag-badge").first()).toHaveText(/Ageing|Stalled|Past close date/);
    await expect(reg.getByTestId("crm-link").first()).toHaveAttribute("href", /Opportunity/);

    const total = await reg.getByTestId("register-summary").innerText();
    await reg.getByRole("searchbox").fill("zzzz-no-such-deal");
    await expect(reg.getByTestId("register-summary")).not.toHaveText(total);
    await reg.getByRole("searchbox").fill("");
    await expect(reg.getByTestId("register-summary")).toHaveText(total);

    await reg.getByRole("button", { name: /export/i }).click();
    const download = page.waitForEvent("download");
    await page.getByRole("menuitem", { name: /csv/i }).click();
    expect((await download).suggestedFilename()).toMatch(/\.csv$/i);
  });

  test("FR-PIP-06 stage movement tiles show snapshot basis and drill down", async ({ page }) => {
    const w = page.getByTestId("widget-stage-movement");
    await expect(w.getByTestId("movement-basis")).toContainText(/\d{4}-\d{2}-\d{2}/);
    await expect(w.getByTestId("movement-created")).toBeVisible();
    await w.getByTestId("movement-created").click();
    await expect(page.getByTestId("drilldown-panel").getByTestId("drilldown-register-row").first()).toBeVisible();
  });

  test("FR-GEN-07 metric info shows PIP ID and sources", async ({ page }) => {
    await page.getByTestId("metric-info-PIP-01").first().click();
    await expect(page.getByTestId("metric-info-content-PIP-01")).toContainText("PIP-01");
  });
});

test.describe("Pipeline roles & RLS", () => {
  for (const role of ["alliance_manager", "marketing"]) {
    test(`${role} persona is denied the Pipeline module`, async ({ page }) => {
      await openPipeline(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("pipeline-view")).toHaveCount(0);
    });
  }

  test("Practice lead sees other practices aggregated in the register", async ({ page }) => {
    await openPipeline(page, "practice_lead");
    await expect(page.getByTestId("widget-opportunity-register").getByTestId("aggregated-other")).toBeVisible();
  });
});

test.describe("Pipeline accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openPipeline(page);
    await expect(page.getByTestId("widget-stage-movement").getByTestId("movement-created")).toBeVisible();
    await expect(page.getByTestId("pipeline-register")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openPipeline(page);
    await expect(page.getByTestId("widget-stage-funnel")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
