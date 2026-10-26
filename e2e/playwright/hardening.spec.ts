import { expect, test, type Page } from "@playwright/test";

/**
 * Cross-module hardening (Step 8): AC-02 all module views + drill-down, AC-03 persona gating with
 * restricted panels absent (not greyed), AC-07 390px without horizontal overflow.
 * Paths and test IDs match the app routes (components/layout/modules.ts) and the module specs.
 * Drill triggers are taken from the per-module specs; Offerings, Accounts and Partners cover
 * their own drill-downs in offerings/accounts/partners.spec.ts.
 */
const ALL_MODULE_VIEWS = [
  { path: "/executive", testId: "executive-view", drillTrigger: "[data-testid='runway-seg-booked']" },
  { path: "/pipeline", testId: "pipeline-view", drillTrigger: "[data-testid='movement-created']" },
  { path: "/pursuits", testId: "pursuits-view", drillTrigger: "[data-testid='bid-no_bid_rate']" },
  { path: "/offerings", testId: "offerings-view", drillTrigger: null },
  { path: "/accounts", testId: "accounts-view", drillTrigger: null },
  { path: "/partners", testId: "partners-view", drillTrigger: null },
  {
    path: "/solutions-capacity",
    testId: "capacity-view",
    drillTrigger: "[data-testid^='architect-RES-']",
  },
  {
    path: "/market-signals",
    testId: "market-signals-view",
    drillTrigger: "[data-testid='funnel-stage-created']",
  },
  { path: "/admin", testId: "admin-view", drillTrigger: null },
] as const;

async function asRole(page: Page, role: string, path: string) {
  await page.goto(path);
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

test("AC-02: all 9 module views render and analytical views open the drill-down panel", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await asRole(page, "gtm_lead", "/executive");

  for (const mod of ALL_MODULE_VIEWS) {
    await page.goto(mod.path);
    await expect(page.getByTestId(mod.testId)).toBeVisible();

    if (mod.drillTrigger) {
      await page.locator(mod.drillTrigger).first().click();
      const panel = page.getByRole("dialog");
      await expect(panel).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(panel).toHaveCount(0);
    }
  }
});

test("AC-03: persona gating enforces module visibility; restricted panels are absent, not greyed", async ({
  page,
}) => {
  await page.setViewportSize({ width: 1440, height: 900 });

  // GTM Lead (restricted persona) sees PUR-06 margin.
  await asRole(page, "gtm_lead", "/pursuits");
  await expect(page.getByTestId("pursuits-view")).toBeVisible();
  await expect(page.getByTestId("widget-margin")).toBeVisible();

  // Practice Lead (non-restricted) -> PUR-06 is absent. A user holds one persona per login, so
  // the persona is established per session (no in-app switcher) and the page reloaded.
  await asRole(page, "practice_lead", "/pursuits");
  await expect(page.getByTestId("persona-badge")).toBeVisible();
  await expect(page.getByTestId("pursuits-view")).toBeVisible();
  await expect(page.getByTestId("widget-margin")).toHaveCount(0);

  // Solutions Lead -> Capacity is accessible and CAP-03 cost of sale is absent.
  await asRole(page, "solutions_lead", "/solutions-capacity");
  await expect(page.getByTestId("capacity-view")).toBeVisible();
  await expect(page.getByTestId("widget-cost-of-sale")).toHaveCount(0);
});

test("AC-07: all 9 modules render cleanly at 390px mobile viewport without horizontal overflow", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await asRole(page, "gtm_lead", "/executive");

  for (const mod of ALL_MODULE_VIEWS) {
    await page.goto(mod.path);
    await expect(page.getByTestId(mod.testId)).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, `Horizontal overflow on ${mod.path}`).toBeLessThanOrEqual(4);
  }
});
