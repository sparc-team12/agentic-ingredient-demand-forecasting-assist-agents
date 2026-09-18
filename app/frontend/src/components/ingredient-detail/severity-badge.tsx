// Shared severity badge (ACRI-41 US-006 / ACRI-64 US-029): a colored badge
// AND the exact text "Critical"/"High"/"Low" together — severity is never
// conveyed by color alone. Reuses the `.badge`/`.badge--warning` structure
// (see `styles.css`), just with a couple more color variants.
import type { RiskSeverity } from "@/lib/risk-api";

interface SeverityBadgeProps {
  severity: RiskSeverity;
}

const SEVERITY_CLASS: Record<RiskSeverity, string> = {
  Critical: "badge badge--critical",
  High: "badge badge--high",
  Low: "badge badge--low",
};

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  return <span className={SEVERITY_CLASS[severity]}>{severity}</span>;
}
