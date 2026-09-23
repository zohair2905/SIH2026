import type { ReactNode } from "react";

export function PageHeading({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {children}
        </div>
      )}
    </div>
  );
}