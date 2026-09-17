import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Panel({
  icon: Icon,
  title,
  subtitle,
  actions,
  className,
  children,
}: {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  className?: string;
  children?: ReactNode;
}) {
  return (
    <section
      className={cn(
        "rounded-lg border border-border bg-card shadow-sm",
        className
      )}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div className="flex items-center gap-3">
          {Icon && <Icon className="size-5 text-primary" />}
          <div>
            <h3 className="text-base font-semibold text-card-foreground">
              {title}
            </h3>
            {subtitle && (
              <p className="mt-0.5 text-xs text-muted-foreground">
                {subtitle}
              </p>
            )}
          </div>
        </div>
        {actions}
      </div>
      {children}
    </section>
  );
}