"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff, LockKeyhole, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { login } from "@/lib/api/auth";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!email || !password) {
      toast.error("Enter your user ID / email and password.");
      return;
    }

    setSubmitting(true);

    const result = await login({ email, password });

    setSubmitting(false);

    if (!result.ok) {
      toast.error(result.error ?? "Sign in failed.");
      return;
    }

    router.replace("/dashboard");
  };

  return (
    <div className="flex min-h-screen flex-col bg-background min-[851px]:flex-row">
      <div className="flex min-h-[45vh] flex-col bg-navy px-[30px] py-[30px] text-white min-[851px]:min-h-screen min-[851px]:w-[52%] min-[851px]:px-[60px] min-[851px]:py-[45px]">
        <div className="flex items-center gap-[14px]">
          <ShieldCheck className="size-[38px] shrink-0" />
          <div>
            <h3 className="text-xl font-semibold">Government of India</h3>
            <p className="text-sm text-white/80">
              Ministry of Home Affairs
            </p>
          </div>
        </div>

        <div className="my-auto max-w-[650px] max-[850px]:mt-[50px] max-[850px]:mb-[20px]">
          <div className="mb-[30px] flex size-[85px] items-center justify-center rounded-[18px] border border-white/30">
            <ShieldCheck className="size-[55px]" />
          </div>

          <h1 className="text-[30px] leading-[1.15] mb-5 font-semibold min-[851px]:text-[42px]">
            Predictive Cybercrime
            <br />
            Intelligence Platform
          </h1>

          <p className="text-[18px] text-white/85">
            From Complaints to Actionable Intelligence
          </p>

          <div className="my-[30px] h-[3px] w-[70px] bg-white" />

          <p className="text-[15px] text-white/80">
            Safer Citizens <span className="mx-[10px]">•</span> Safer India
          </p>
        </div>
      </div>

      <div className="flex min-h-[55vh] flex-col items-center justify-center px-[25px] py-[25px] min-[851px]:w-[48%] min-[851px]:px-[40px] min-[851px]:py-[40px]">
        <div className="w-full max-w-[470px] rounded-[14px] bg-card p-[42px] shadow-[0_8px_30px_rgba(0,0,0,0.08)]">
          <div className="mb-5 flex size-12 items-center justify-center rounded-[10px] bg-[#eaf2f9] text-[#0b4f82]">
            <LockKeyhole className="size-[25px]" />
          </div>

          <h2 className="mb-2 text-[30px] font-semibold text-[#162b3d]">
            Sign in
          </h2>

          <p className="mb-6 text-[14px] leading-[1.6] text-[#687786]">
            Access for authorized government and law enforcement personnel
            only.
          </p>

          <form onSubmit={handleLogin} className="space-y-0">
            <div className="mb-4">
              <Label
                htmlFor="email"
                className="mb-2 block text-[14px] font-semibold text-[#263746]"
              >
                User ID / Official Email
              </Label>
              <Input
                id="email"
                type="text"
                autoComplete="username"
                placeholder="Enter your user ID or email"
                className="h-12 rounded-[7px] border-[#ccd6df] px-[14px] text-[14px]"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div className="mb-4">
              <Label
                htmlFor="password"
                className="mb-2 block text-[14px] font-semibold text-[#263746]"
              >
                Password
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  className="h-12 rounded-[7px] border-[#ccd6df] px-[14px] pr-12 text-[14px]"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-3 flex items-center text-[#687786]"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="size-[19px]" />
                  ) : (
                    <Eye className="size-[19px]" />
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="mt-[5px] h-[50px] w-full rounded-[7px] text-[15px] font-semibold"
              disabled={submitting}
            >
              {submitting ? "Signing in..." : "Sign In"}
            </Button>
          </form>

          <button
            type="button"
            className="mx-auto my-4 block text-[14px] text-[#0b4f82]"
          >
            Forgot password?
          </button>

          <div className="flex items-start gap-[10px] rounded-[7px] bg-[#f5f7f9] p-[14px] text-[12px] leading-[1.5] text-[#687786]">
            <LockKeyhole className="mt-[1px] size-4 shrink-0" />
            <p>Unauthorized access is prohibited and may be subject to legal
            action.</p>
          </div>
        </div>

        <p className="mt-[25px] text-center text-[11px] text-[#7a8792]">
          © 2026 Government of India • Indian Cybercrime Coordination Centre
        </p>
      </div>
    </div>
  );
}