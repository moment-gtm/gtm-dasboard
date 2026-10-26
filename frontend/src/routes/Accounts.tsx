/** Accounts (FR-ACC-01..05) — composes shared components only. */
import { ExportViewButton } from "@/components/common/ExportViewButton";
import { ModuleGate } from "@/components/common/ModuleGate";
import {
  HeadlineScorecard,
  HeadlineSpotlight,
  toHeadlines,
} from "@/components/common/ModuleHeadlines";
import { BentoGrid, BentoItem, BentoRow } from "@/components/layout/BentoGrid";
import { AccountDetailPanel } from "@/components/widgets/accounts/AccountDetailPanel";
import { AccountPlanHealth } from "@/components/widgets/accounts/AccountPlanHealth";
import { ExpansionVsNewLogo } from "@/components/widgets/accounts/ExpansionVsNewLogo";
import { PenetrationMatrix } from "@/components/widgets/accounts/PenetrationMatrix";
import { WhitespaceSummary } from "@/components/widgets/accounts/WhitespaceSummary";
import {
  useExpansion,
  usePenetration,
  usePlanHealth,
  useWhitespace,
} from "@/hooks/useAccountsData";

const useHeadlines = () =>
  toHeadlines([usePenetration(), useWhitespace(), useExpansion(), usePlanHealth()]);

export function Accounts() {
  return (
    <ModuleGate
      moduleKey="accounts"
      eyebrow="Account growth"
      title="Accounts"
      description="Practice penetration, whitespace, expansion versus new logo and account-plan health."
      highlights={<HeadlineScorecard label="Accounts scorecard" useHeadlines={useHeadlines} />}
      actions={<ExportViewButton module="accounts" />}
    >
      <div data-testid="accounts-view">
        <BentoGrid>
          <BentoRow>
            <BentoItem span={8}>
              <PenetrationMatrix />
            </BentoItem>
            <BentoItem span={4} sticky>
              <HeadlineSpotlight useHeadlines={useHeadlines} />
            </BentoItem>
          </BentoRow>
          <BentoItem span={6}>
            <WhitespaceSummary />
          </BentoItem>
          <BentoItem span={6}>
            <ExpansionVsNewLogo />
          </BentoItem>
          <BentoItem span={12}>
            <AccountPlanHealth />
          </BentoItem>
        </BentoGrid>
      </div>
      <AccountDetailPanel />
    </ModuleGate>
  );
}
