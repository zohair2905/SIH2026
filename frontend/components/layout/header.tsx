import { Bell, ShieldCheck } from "lucide-react";

export function Header() {
  return (
    <header className="bg-navy text-white">
      <div className="mx-auto flex max-w-[1360px] items-center justify-between gap-6 px-6 py-3.5">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-lg bg-white/10">
            <ShieldCheck className="size-6" />
          </div>
          <div className="leading-tight">
            <strong className="block text-sm">Cyber Intelligence Team</strong>
            <span className="block text-xs text-white/70">
              Predictive Analytics Division
            </span>
          </div>
        </div>

        <div className="hidden text-center lg:block">
          <h2 className="text-base font-semibold tracking-wide">
            Predictive Cybercrime Intelligence Platform
          </h2>
          <p className="text-xs text-white/70">
            From Complaints to Actionable Intelligence
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden text-right leading-tight xl:block">
            <strong className="block text-xs">
              Safer Citizens | Safer India
            </strong>
            <span className="block text-[11px] text-white/70">
              सुरक्षित नागरिक | सुरक्षित भारत
            </span>
          </div>

          <div className="hidden h-8 w-px bg-white/20 md:block" />

          <div className="relative">
            <Bell className="size-5" />
            <span className="absolute -right-2 -top-2 flex size-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold">
              3
            </span>
          </div>

          <div className="flex items-center gap-2.5">
            <div className="flex size-9 items-center justify-center rounded-full bg-white/15 text-sm font-bold">
              AP
            </div>
            <div className="hidden leading-tight sm:block">
              <strong className="block text-xs">Insp. A. Patil</strong>
              <span className="block text-[11px] text-white/70">
                Maharashtra Police
              </span>
            </div>
            <span className="hidden text-white/70 sm:block">⌄</span>
          </div>
        </div>
      </div>
    </header>
  );
}