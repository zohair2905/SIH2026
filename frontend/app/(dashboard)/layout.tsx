import { Suspense } from "react";

import { AuthGuard } from "@/components/layout/auth-guard";
import { Header } from "@/components/layout/header";
import { TopNav } from "@/components/layout/top-nav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen flex-col bg-background">
        <Header />
        <Suspense fallback={null}>
          <TopNav />
        </Suspense>
        <main className="mx-auto w-full max-w-[1360px] flex-1 px-6 py-6">
          {children}
        </main>
      </div>
    </AuthGuard>
  );
}