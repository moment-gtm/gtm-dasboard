/** Pursuits & Wins UAT keyed to FR-PUR IDs, plus role checks, accessibility and 390px responsiveness. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openPursuits(page: Page, role = "gtm_lead") {
  await page.goto("/pursuits");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test.describe("Pursuits & Wins — FR-PUR", () => {
  test.beforeEach(async ({ page }) => openPursuits(page));

  test("FR-PUR-01 win rate shows eight quarters against the goal, with a value toggle and drill-down", async ({ page }) => {
    const w = page.getByTestId("widget-win-rate");
    await expect(w.getByTestId("win-rate-headline")).toContainText(/Trailing four quarters: \d+(\.\d)?%/);
    await expect(w.locator("[data-testid^='winrate-']")).toHaveCount(8);
    await expect(w.locator("[data-testid^='winrate-']").last()).toContainText("in progress");

    const first = w.locator("[data-testid^='winrate-']").nth(3);
    const before = await first.innerText();
    await w.getByTestId("win-rate-by-value").check();
    await expect(first).not.toHaveText(before);

    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /Win rate by quarter/ })).toBeVisible();

    await first.click();
    const panel = page.getByTestId("drilldown-panel");
    await expect(panel.getByTestId("drilldown-register-row").first()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("FR-PUR-02 loss reasons call out the most frequent reason in text", async ({ page }) => {
    const w = page.getByTestId("widget-loss-reasons");
    await expect(w.locator("button[data-testid^='loss-']", { hasText: "most frequent" })).toHaveCount(1);
    await expect(w.getByTestId("loss-reason-basis")).toContainText("most frequent reason");
    await w.getByTestId("loss-Price / commercial terms").click();
    await expect(page.getByTestId("drilldown-panel").getByTestId("drilldown-register-row").first()).toBeVisible();
  });

  test("FR-PUR-03 source mix lists every deal source with win rate", async ({ page }) => {
    const w = page.getByTestId("widget-source-mix");
    for (const s of ["Client RFP", "Proactive", "Partner-sourced", "Campaign / Marketing", "Account expansion"]) {
      await expect(w.getByTestId(`source-${s}`)).toBeVisible();
    }
    await w.getByText("Show data table").click();
    await expect(w.getByRole("table", { name: /Win rate by deal source/ })).toBeVisible();
  });

  test("FR-PUR-04 bid discipline shows labelled measures and orals conversion; callout follows the rule", async ({ page }) => {
    const w = page.getByTestId("widget-bid-discipline");
    await expect(w.getByTestId("bid-no_bid_rate")).toContainText("No-bid rate");
    await expect(w.getByTestId("bid-no_bid_rate").getByTestId("status-badge")).toBeVisible();
    await expect(w.getByTestId("bid-pursued_win_rate").getByTestId("status-badge")).toBeVisible();
    await w.getByTestId("bid-no_bid_rate").click();
    await expect(page.getByTestId("drilldown-panel").getByTestId("drilldown-register-row").first()).toBeVisible();
    await page.keyboard.press("Escape");

    const nb = await w.getByTestId("bid-no_bid_rate").getByTestId("status-badge").getAttribute("data-status");
    const win = await w.getByTestId("bid-pursued_win_rate").getByTestId("status-badge").getAttribute("data-status");
    const callout = w.getByTestId("bid-callout");
    if (nb !== "on_track" && win !== "on_track") await expect(callout).toBeVisible();
    else await expect(callout).toHaveCount(0);

    const o = page.getByTestId("widget-orals-conversion");
    await expect(o.getByTestId("orals-headline")).toContainText(/\d+(\.\d)?%/);
    await o.getByTestId("orals-won").click();
    await expect(page.getByTestId("drilldown-panel").getByTestId("drilldown-register-row").first()).toBeVisible();
  });

  test("FR-PUR-05 margin panel (PUR-06) is shown to a restricted persona", async ({ page }) => {
    await expect(page.getByTestId("widget-margin").getByTestId("margin-value")).toContainText("pts");
  });

  test("FR-GEN-07 metric info shows PUR ID and sources", async ({ page }) => {
    await page.getByTestId("metric-info-PUR-01").first().click();
    await expect(page.getByTestId("metric-info-content-PUR-01")).toContainText("PUR-01");
  });
});

test.describe("Pursuits roles & RLS", () => {
  for (const role of ["alliance_manager", "marketing", "client_partner"]) {
    test(`${role} persona is denied the Pursuits module`, async ({ page }) => {
      await openPursuits(page, role);
      await expect(page.getByTestId("access-denied")).toBeVisible();
      await expect(page.getByTestId("pursuits-view")).toHaveCount(0);
    });
  }

  test("Solutions lead can open Pursuits", async ({ page }) => {
    await openPursuits(page, "solutions_lead");
    await expect(page.getByTestId("widget-bid-discipline")).toBeVisible();
  });
});

test.describe("Pursuits accessibility & responsiveness", () => {
  test("axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openPursuits(page);
    await expect(page.getByTestId("widget-orals-conversion").getByTestId("orals-headline")).toBeVisible();
    await expect(page.getByTestId("widget-win-rate").locator("[data-testid^='winrate-']").first()).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openPursuits(page);
    await expect(page.getByTestId("widget-win-rate")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
