/** Administration & Governance UAT (FR-ADM) — role gating, governed edits with audit, DQ console, change control, a11y. */
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

async function openAdmin(page: Page, role = "gtm_lead", path = "/admin") {
  await page.goto(path);
  await page.evaluate((r) => {
    sessionStorage.setItem("gtm-role", JSON.stringify({ state: { role: r }, version: 0 }));
    sessionStorage.removeItem("gtm-filters");
  }, role);
  await page.reload();
}

const H = (role: string) => ({ "X-Mock-Role": role });

test.describe("Administration — access", () => {
  for (const role of ["gtm_lead", "sales_ops"]) {
    test(`${role} can open Administration`, async ({ page }) => {
      await openAdmin(page, role);
      await expect(page.getByTestId("admin-view")).toBeVisible();
      await expect(page.getByRole("tab")).toHaveCount(7);
    });
  }

  test("other personas are denied the page and the API but can manage their own alert subscriptions", async ({
    page,
    request,
  }) => {
    await openAdmin(page, "practice_lead");
    await expect(page.getByTestId("access-denied")).toBeVisible();
    await expect(page.getByTestId("widget-alert-subscriptions")).toBeVisible();
    const res = await request.get("/api/admin/audit", { headers: H("practice_lead") });
    expect(res.status()).toBe(403);
  });

  test("tabs are keyboard operable", async ({ page }) => {
    await openAdmin(page);
    await page.getByTestId("tab-targets").focus();
    await page.keyboard.press("ArrowRight");
    await expect(page.getByTestId("tab-thresholds")).toHaveAttribute("aria-selected", "true");
    await expect(page.getByTestId("widget-thresholds")).toBeVisible();
  });
});

test.describe("Administration — governed edits", () => {
  test("FR-ADM-02 threshold edit needs a reason, is versioned and audited; then reverted", async ({ page, request }) => {
    const list = await (await request.get("/api/admin/thresholds", { headers: H("gtm_lead") })).json();
    const row = list[0];
    const id = row.metric_id as string;
    const orig = { on_track: row.on_track as number, watch: row.watch as number };
    const delta = row.direction === "higher" ? -0.01 : 0.01;
    const edited = { on_track: orig.on_track + delta, watch: orig.watch };
    try {
      await openAdmin(page);
      await page.getByTestId("tab-thresholds").click();
      await page.getByRole("button", { name: `Edit ${id} thresholds` }).click();
      const form = page.getByTestId(`threshold-form-${id}`);
      await expect(form).toBeVisible();

      const bad = await request.put(`/api/admin/thresholds/${id}`, {
        headers: H("gtm_lead"),
        data: { ...edited, reason: "" },
      });
      expect(bad.status()).toBe(422);

      const ok = await request.put(`/api/admin/thresholds/${id}`, {
        headers: H("gtm_lead"),
        data: { ...edited, reason: "UAT edit" },
      });
      expect(ok.ok()).toBeTruthy();

      await page.getByTestId("tab-audit").click();
      await expect(page.getByTestId("audit-table")).toContainText("admin.threshold.edit");
    } finally {
      await request.put(`/api/admin/thresholds/${id}`, {
        headers: H("gtm_lead"),
        data: { ...orig, reason: "UAT revert" },
      });
    }
    const hist = await (await request.get(`/api/admin/thresholds/${id}/history`, { headers: H("gtm_lead") })).json();
    expect(hist.length).toBeGreaterThanOrEqual(3);
  });

  test("FR-ADM-01 targets show the active version and a full grid", async ({ page }) => {
    await openAdmin(page);
    await expect(page.getByTestId("widget-targets")).toBeVisible();
    await expect(page.getByTestId("active-target-version")).toContainText(/FY\d\d/);
    await expect(page.getByTestId("target-grid")).toBeVisible();
    await expect(page.getByTestId("target-review")).toBeDisabled();
  });

  test("FR-ADM-03 reference data: in-use values cannot be removed; read-only sets reject edits", async ({ page, request }) => {
    const sets = await (await request.get("/api/admin/reference", { headers: H("gtm_lead") })).json();
    expect(JSON.stringify(sets)).toContain("verticals");
    const ro = await request.put("/api/admin/reference/offerings", { headers: H("gtm_lead"), data: { values: [], reason: "UAT" } });
    expect(ro.status()).toBe(405);
    const cur = await (await request.get("/api/admin/reference/verticals", { headers: H("gtm_lead") })).json();
    const values: string[] = cur.values;
    const rm = await request.put("/api/admin/reference/verticals", {
      headers: H("gtm_lead"),
      data: { values: values.slice(1), reason: "UAT" },
    });
    expect(rm.status()).toBe(409);
    await openAdmin(page);
    await page.getByTestId("tab-reference").click();
    await expect(page.getByTestId("tab-reference")).toHaveAttribute("aria-selected", "true");
  });
});

test.describe("Administration — data quality and change control", () => {
  test("FR-ADM-04 DQ console lists nine rules, the ADM-01 gate and exports findings", async ({ page }) => {
    await openAdmin(page);
    await page.getByTestId("tab-dq").click();
    await expect(page.getByTestId("adm01-value")).toContainText("%");
    await expect(page.getByTestId("gate-status")).toContainText(/met/);
    await expect(page.locator("[data-testid^='dq-rule-']")).toHaveCount(9);
    await expect(page.getByTestId("dq-rule-DQ-09")).toContainText("Released asset build item missing");
    await expect(page.getByTestId("dq-rule-DQ-09")).not.toContainText("Not active");
    await expect(page.getByTestId("dq-findings").locator("tbody tr").first()).toBeVisible();
    await expect(page.getByTestId("dq-export")).toHaveAttribute("href", /\/api\/admin\/dq\/export/);
  });

  test("change request: log, assess by both roles, approve, release", async ({ page, request }) => {
    const title = `UAT definition change ${Date.now()}`;
    await openAdmin(page);
    await page.getByTestId("tab-change").click();
    await page.getByTestId("cr-title").fill(title);
    await page.getByLabel("What should change and why").fill("Align win-rate definition");
    await page.getByTestId("cr-submit").click();
    const item = page.locator("li[data-testid^='cr-']", { hasText: title });
    await expect(item).toBeVisible();
    const id = (await item.getAttribute("data-testid"))!.replace("cr-", "");

    const a1 = await request.post(`/api/admin/change-requests/${id}/assess`, { headers: H("gtm_lead"), data: { note: "Assessed" } });
    expect(a1.ok()).toBeTruthy();
    const early = await request.post(`/api/admin/change-requests/${id}/decide`, {
      headers: H("gtm_lead"),
      data: { decision: "approve", note: "Approved" },
    });
    expect(early.ok()).toBeFalsy();
    await request.post(`/api/admin/change-requests/${id}/assess`, { headers: H("sales_ops"), data: { note: "Assessed" } });
    const denied = await request.post(`/api/admin/change-requests/${id}/decide`, {
      headers: H("sales_ops"),
      data: { decision: "approve", note: "Approved" },
    });
    expect(denied.ok()).toBeFalsy();

    await page.reload();
    await page.getByTestId("tab-change").click();
    await page.getByTestId(`cr-approve-${id}`).waitFor();
    await item.getByLabel("Note").fill("Approved");
    await page.getByTestId(`cr-approve-${id}`).click();
    await expect(page.getByTestId(`cr-status-${id}`)).toHaveText("Approved");
    await page.getByTestId(`cr-release-${id}`).click();
    await expect(page.getByTestId(`cr-status-${id}`)).toHaveText("Released");
  });
});

test.describe("Administration — alerts & digest (FR-ALR-01..03)", () => {
  test("FR-ALR-02 threshold alert rules show live semantic status and matching deals", async ({ page }) => {
    await openAdmin(page);
    await page.getByTestId("tab-alerts").click();
    const rules = page.getByTestId("widget-alert-rules");
    await expect(rules).toBeVisible();
    await expect(rules.getByTestId("alert-rule-row-coverage_drop")).toBeVisible();
    await expect(rules.getByTestId("alert-rule-row-large_deal_slip")).toBeVisible();
    await expect(rules.getByTestId("alert-rule-row-unvalidated_ai_propose")).toBeVisible();
    await expect(rules.getByTestId("alert-rule-deals-large_deal_slip")).toBeVisible();
  });

  test("FR-ALR-03 alert subscriptions allow toggling email and Teams channels", async ({ page }) => {
    await openAdmin(page);
    await page.getByTestId("tab-alerts").click();
    const subs = page.getByTestId("widget-alert-subscriptions");
    await expect(subs).toBeVisible();
    const checkbox = subs.getByTestId("sub-teams-weekly_digest");
    await expect(checkbox).toBeVisible();
    const before = await checkbox.isChecked();
    await checkbox.click();
    await expect(checkbox).toHaveJSProperty("checked", !before);
    await checkbox.click();
    await expect(checkbox).toHaveJSProperty("checked", before);
  });

  test("FR-ALR-01 weekly digest previews KPIs, attention deals, over-capacity architects, and logs dispatch", async ({
    page,
  }) => {
    await openAdmin(page);
    await page.getByTestId("tab-alerts").click();
    const digest = page.getByTestId("widget-digest-config");
    await expect(digest).toBeVisible();
    await expect(digest.getByTestId("digest-kpi-summary")).toContainText("EXE-01");
    await expect(digest.getByTestId("digest-highlights")).toContainText("EXE-10");
    await expect(digest.getByTestId("digest-highlights")).toContainText("CAP-01");
    await expect(digest.getByTestId("digest-email-preview")).toContainText("Moment GTM Weekly Digest");
    await expect(digest.getByTestId("digest-teams-preview")).toContainText("#moment-gtm-leadership");

    await digest.getByTestId("digest-send-now").click();
    await expect(digest.getByTestId("digest-history-table")).toBeVisible();
    await expect(digest.getByTestId("digest-history-table")).toContainText("delivered");
  });
});

test.describe("Administration — accessibility and layout", () => {
  for (const tab of ["targets", "thresholds", "reference", "dq", "change", "alerts", "audit"]) {
    test(`no axe violations on ${tab}`, async ({ page }) => {
      await openAdmin(page);
      await page.getByTestId(`tab-${tab}`).click();
      await expect(page.getByRole("tabpanel")).toBeVisible();
      await page.waitForLoadState("networkidle");
      const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      expect(r.violations.map((v) => `${v.id}: ${v.nodes[0]?.target}`)).toEqual([]);
    });
  }

  test("390px: no horizontal page scroll", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openAdmin(page);
    await page.waitForLoadState("networkidle");
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(overflow).toBe(false);
  });
});
