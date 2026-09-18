"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  FileText,
  LayoutDashboard,
  Map,
  ScrollText,
  Search,
  TrendingUp,
  Users,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { isAdmin, useSession } from "@/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/cases", label: "Cases", icon: FileText },
  { href: "/predictions", label: "Predictions", icon: TrendingUp },
  { href: "/gis", label: "GIS Intelligence", icon: Map },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/reports", label: "Reports", icon: ScrollText },
  { href: "/users", label: "Users", icon: Users, adminOnly: true },
  { href: "/audit-logs", label: "Audit Logs", icon: ScrollText, adminOnly: true },
];

export function TopNav() {
  const pathname = usePathname();
  const session = useSession();
  const visibleItems = navItems.filter(
    (item) => !item.adminOnly || isAdmin(session?.role)
  );

  return (
    <nav className="bg-navy-deep text-white">
      <div className="mx-auto flex max-w-[1360px] items-center justify-between gap-6 px-6">
        <div className="flex flex-1 flex-wrap items-center">
          {visibleItems.map(({ href, label, icon: Icon }) => {
            const isActive =
              pathname === href || pathname.startsWith(`${href}/`);

            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm transition-colors",
                  isActive
                    ? "bg-white/15 font-semibold text-white"
                    : "text-white/75 hover:bg-white/5 hover:text-white"
                )}
              >
                {Icon && <Icon className="size-4" />}
                <span className="hidden items-center gap-2 md:flex">
                  {label}
                </span>
              </Link>
            );
          })}
        </div>

        <div className="relative hidden md:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/60" />
          <input
            type="text"
            placeholder="Search cases, locations, accounts..."
            className="w-64 rounded-md border border-white/15 bg-white/10 py-2 pl-9 pr-3 text-sm text-white placeholder:text-white/60 focus:border-white/30 focus:outline-none"
          />
        </div>
      </div>
    </nav>
  );
}