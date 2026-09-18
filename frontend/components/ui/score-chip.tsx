import { cn } from "@/lib/utils";
import type { ConfidenceLevel, SeverityLevel } from "@/types";

export function ScoreChip({
  score,
  level,
  className,
}: {
  score: string;
  level: SeverityLevel;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-5 w-fit shrink-0 items-center justify-center overflow-hidden rounded-md border border-transparent px-2 py-0.5 text-xs font-semibold whitespace-nowrap",
        level === "high" && "bg-risk-bg text-risk",
        level === "medium" && "bg-risk-med-bg text-risk-med",
        level === "low" && "bg-risk-low-bg text-risk-low",
        level === "critical" && "bg-risk-critical-bg text-risk-critical",
        className
      )}
    >
      {score}
    </span>
  );
}

export function ConfidenceChip({
  level,
  className,
}: {
  level: ConfidenceLevel;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex h-5 w-fit shrink-0 items-center justify-center overflow-hidden rounded-md border border-transparent px-2 py-0.5 text-xs font-semibold whitespace-nowrap",
        level === "high" && "bg-risk-bg text-risk",
        level === "medium" && "bg-risk-med-bg text-risk-med",
        level === "low" && "bg-risk-low-bg text-risk-low",
        className
      )}
    >
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </span>
  );
}