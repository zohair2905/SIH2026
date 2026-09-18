"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getMe } from "@/lib/api/auth";
import { clearSession } from "@/lib/auth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let mounted = true;

    getMe().then((result) => {
      if (!mounted) {
        return;
      }

      if (!result.ok) {
        clearSession();
        router.replace("/login");
        return;
      }

      setChecked(true);
    });

    return () => {
      mounted = false;
    };
  }, [router]);

  if (!checked) {
    return null;
  }

  return <>{children}</>;
}