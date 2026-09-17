import { Badge } from "@/components/ui/badge";
import type { AlertStatus, CaseStatus } from "@/types";

export type { AlertStatus, CaseStatus };

const variantByStatus: Record<
  CaseStatus | AlertStatus,
  "statusNew" | "statusAcknowledged" | "statusInvestigating" | "statusResolved"
> = {
  new: "statusNew",
  acknowledged: "statusAcknowledged",
  investigating: "statusInvestigating",
  resolved: "statusResolved",
  unacknowledged: "statusNew",
};

const labelByStatus: Record<CaseStatus | AlertStatus, string> = {
  new: "New",
  acknowledged: "Acknowledged",
  investigating: "Investigating",
  resolved: "Resolved",
  unacknowledged: "Unacknowledged",
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