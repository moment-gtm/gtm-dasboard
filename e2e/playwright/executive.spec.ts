/**
 * Executive summary UAT (AC-02) keyed to FR IDs, plus role checks (AC-03), accessibility (AC-07)
 * and the 390px responsiveness check (NFR-09 / FR-GEN-12).
 */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openExecutive(page: Page, role = "gtm_lead") {
  await page.goto("/executive");
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
    sessionStorage.removeItem("gtm-metric-ids");
  }, role);
  await page.reload();
}

test.describe("Executive summary — FR-EXE", () => {
  test.beforeEach(async ({ page }) => openExecutive(page));

  test("FR-EXE-01 bookings runway with markers and narrative", async ({ page }) => {
    const w = page.getByTestId("widget-runway");
    await expect(w.getByTestId("runway-seg-booked")).toBeVisible();
    await expect(w.getByTestId("runway-seg-commit")).toBeVisible();
    await expect(w.getByTestId("runway-seg-best_case")).toBeVisible();
    await expect(w.getByTestId("runway-legend")).toContainText("Plan pace");
    await expect(w.getByTestId("runway-legend")).toContainText("FY target");
    await expect(w.getByTestId("runway-narrative")).toHaveText(/(ahead of|behind) (plan )?pace/i);
  });

  test("FR-EXE-02 six KPIs with value, status and sparkline", async ({ page }) => {
    for (const id of ["EXE-01", "EXE-02", "EXE-03", "EXE-04", "EXE-05", "EXE-06"]) {
      const card = page.getByTestId(`kpi-${id}`);
      await expect(card).toBeVisible();
      await expect(card.getByTestId("sparkline")).toBeVisible();
    }
  });

  test("FR-EXE-03 bookings by quarter marks QTD", async ({ page }) => {
    const w = page.getByTestId("widget-bookings-by-quarter");
    await expect(w).toContainText("QTD");
    await expect(w).toContainText(/Met|Missed/);
  });

  test("FR-EXE-04 pipeline by vertical split", async ({ page }) => {
    const w = page.getByTestId("widget-pipeline-by-vertical");
    await expect(w).toContainText("Qualified");
    await expect(w).toContainText("Identify");
  });

  test("FR-EXE-05 deals needing attention flags", async ({ page }) => {
    const w = page.getByTestId("widget-deals-attention");
    await expect(w.getByTestId("attention-tile")).toHaveCount(3);
    await expect(w.getByRole("table", { name: /by vertical and reason/ })).toBeVisible();
    await w.getByTestId("attention-toggle-register").click();
    await expect(w.getByTestId("attention-register-row").first()).toBeVisible();
    await expect(w.getByTestId("flag-badge").first()).toHaveText(/Ageing|Stalled|Past close date/);
    await expect(w.getByTestId("crm-link").first()).toHaveAttribute("href", /Opportunity/);
  });
});

test.describe("Global behaviour — FR-GEN", () => {
  test.beforeEach(async ({ page }) => openExecutive(page));

  test("FR-GEN-05 status shown as text, not colour alone", async ({ page }) => {
    const badge = page.getByTestId("status-badge").first();
    await expect(badge).toHaveText(/On track|Watch|Off track/);
  });

  test("FR-GEN-02 filters refetch and persist across modules", async ({ page }) => {
    const before = await page.getByTestId("kpi-value-EXE-01").innerText();
    await page.getByTestId("filter-vertical").click();
    await page.getByTestId("filter-option-vertical-BFSI").check();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("filter-count")).toContainText("1 filter");
    await expect(page.getByTestId("kpi-value-EXE-01")).not.toHaveText(before);
    await page.getByTestId("nav-pipeline").click();
    await expect(page.getByTestId("pipeline-view")).toBeVisible();
    await expect(page.getByTestId("filter-count")).toContainText("1 filter");
    await page.getByTestId("nav-executive").click();
    await expect(page.getByTestId("filter-count")).toContainText("1 filter");
  });

  test("FR-GEN-04 pro-rated target badge when filtering below target grain", async ({ page }) => {
    await page.getByTestId("filter-vertical").click();
    await page.getByTestId("filter-option-vertical-BFSI").check();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("prorated-badge").first()).toBeVisible();
  });

  test("FR-GEN-06 drill-down opens from an aggregate and Esc closes", async ({ page }) => {
    await page.getByTestId("runway-seg-booked").click();
    const panel = page.getByTestId("drilldown-panel");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("drilldown-register-row").first()).toBeVisible();
    await expect(panel.getByTestId("crm-link").first()).toHaveAttribute("target", "_blank");
    await page.keyboard.press("Escape");
    await expect(panel).toBeHidden();
  });

  test("FR-GEN-07 metric info shows ID, definition and source, and global toggle shows/hides inline IDs and sources", async ({ page }) => {
    await expect(page.getByTestId("metric-id-chip")).toHaveCount(0);
    await expect(page.getByTestId("metric-sources-chip")).toHaveCount(0);

    await page.getByTestId("toggle-metric-ids").check();
    await expect(page.getByTestId("metric-id-chip").first()).toBeVisible();
    await expect(page.getByTestId("metric-sources-chip").first()).toContainText("SRC-");

    await page.getByTestId("toggle-metric-ids").uncheck();
    await expect(page.getByTestId("metric-id-chip")).toHaveCount(0);

    await page.getByTestId("metric-info-EXE-08").first().click();
    const pop = page.getByTestId("metric-info-content-EXE-08");
    await expect(pop).toContainText("EXE-08");
    await expect(pop).toContainText("Sources:");
    await expect(pop).toContainText("SRC-01");
  });

  test("FR-GEN-09 freshness indicator lists sources", async ({ page }) => {
    await page.getByTestId("freshness-indicator").click();
    await expect(page.getByTestId("freshness-crm")).toBeVisible();
  });
});

test.describe("Roles & RLS — AC-03", () => {
  test("Solutions lead cannot reach the Executive summary", async ({ page }) => {
    await openExecutive(page, "solutions_lead");
    await expect(page.getByTestId("access-denied")).toBeVisible();
    await expect(page.getByTestId("executive-view")).toHaveCount(0);
  });

  test("Client partner sees assigned-account scope", async ({ page }) => {
    await openExecutive(page, "client_partner");
    await expect(page.getByTestId("role-scope")).toContainText(/account/i);
    await expect(page.getByTestId("executive-view")).toBeVisible();
    await expect(page.getByTestId("prorated-badge").first()).toBeVisible();
  });

  test("Practice lead sees other practices aggregated in drill-down", async ({ page }) => {
    await openExecutive(page, "practice_lead");
    await page.getByTestId("runway-seg-booked").click();
    await expect(page.getByTestId("drilldown-panel")).toBeVisible();
    // Scope to the panel: the Deals-needing-attention widget shows its own aggregate note too.
    await expect(page.getByTestId("drilldown-panel").getByTestId("aggregated-other")).toBeVisible();
  });
});

test.describe("Accessibility & responsiveness", () => {
  test("AC-07 axe-core: no serious/critical WCAG 2.1 AA violations", async ({ page }) => {
    await openExecutive(page);
    await expect(page.getByTestId("kpi-EXE-01")).toBeVisible();
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(serious, JSON.stringify(serious.map((v) => [v.id, v.nodes.length]))).toEqual([]);
  });

  test("NFR-09 usable at 390px without horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openExecutive(page);
    await expect(page.getByTestId("kpi-EXE-01")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});
