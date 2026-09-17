"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getSession } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (!getSession()) {
      router.replace("/login");
      return;
    }

    const timer = window.setTimeout(() => setChecked(true), 0);

    return () => window.clearTimeout(timer);
  }, [router]);

  if (!checked) {
    return null;
  }

  return <>{children}</>;
}