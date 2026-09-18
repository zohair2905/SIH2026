import { Badge } from "@/components/ui/badge";
import type { AlertStatus, CaseStatus } from "@/types";

export type { AlertStatus, CaseStatus };

const variantByStatus: Record<
  CaseStatus | AlertStatus,
  "statusNew" | "statusAcknowledged" | "statusInvestigating" | "statusResolved"
> = {
  new: "statusNew",
  open: "statusNew",
  acknowledged: "statusAcknowledged",
  dismissed: "statusAcknowledged",
  investigating: "statusInvestigating",
  resolved: "statusResolved",
  closed: "statusResolved",
};

const labelByStatus: Record<CaseStatus | AlertStatus, string> = {
  new: "New",
  open: "Open",
  acknowledged: "Acknowledged",
  dismissed: "Dismissed",
  investigating: "Investigating",
  resolved: "Resolved",
  closed: "Closed",
};

export function StatusBadge({
  status,
  className,
}: {
  status: CaseStatus | AlertStatus;
  className?: string;
}) {
  return (
    <Badge variant={variantByStatus[status]} className={className}>
      {labelByStatus[status]}
    </Badge>
  );
}