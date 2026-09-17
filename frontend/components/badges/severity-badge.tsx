import { Badge } from "@/components/ui/badge";
import type { SeverityLevel } from "@/types";

const variantByLevel: Record<SeverityLevel, "severityHigh" | "severityMedium" | "severityLow"> = {
  high: "severityHigh",
  medium: "severityMedium",
  low: "severityLow",
};

export function SeverityBadge({
  level,
  className,
}: {
  level: SeverityLevel;
  className?: string;
}) {
  return (
    <Badge variant={variantByLevel[level]} className={className}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  );
}