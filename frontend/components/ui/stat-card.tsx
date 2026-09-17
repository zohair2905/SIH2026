import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

export type StatTone = "blue" | "red" | "orange" | "green";

const toneStyles: Record<
  StatTone,
  { icon: string; value: string }
> = {
  blue: { icon: "bg-blue-100 text-blue-700", value: "text-blue-700" },
  red: { icon: "bg-red-100 text-red-600", value: "text-red-600" },
  orange: { icon: "bg-orange-100 text-orange-700", value: "text-orange-700" },
  green: { icon: "bg-green-100 text-green-700", value: "text-green-700" },
};

export function StatCard({
  icon: Icon,
  tone = "blue",
  value,
  label,
  note,
}: {
  icon?: LucideIcon;
  tone?: StatTone;
  value: string;
  label: string;
  note?: string;
}) {
  const styles = toneStyles[tone];

  return (
    <div className="flex items-center gap-4 rounded-lg border border-border bg-card p-5 shadow-sm">
      {Icon && (
        <div
          className={cn(
            "flex size-13 shrink-0 items-center justify-center rounded-lg",
            styles.icon
          )}
        >
          <Icon className="size-6" />
        </div>
      )}
      <div className="min-w-0">
        <strong
          className={cn(
            "block text-2xl font-semibold leading-tight",
            styles.value
          )}
        >
          {value}
        </strong>
        <span className="block text-sm text-foreground">{label}</span>
        {note && (
          <small className="block text-xs text-muted-foreground">
            {note}
          </small>
        )}
      </div>
    </div>
  );
}