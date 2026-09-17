import type { AlertSummary } from "@/types";

export const initialAlerts: AlertSummary[] = [
  {
    id: "AL-2026-0318",
    time: "15 Sep 2026, 14:32",
    type: "Cash Withdrawal Risk",
    location: "Hadapsar, Pune",
    description:
      "Predicted high-risk cash withdrawal location detected.",
    severity: "high",
    status: "unacknowledged",
    caseId: "CC-2026-4381",
  },
  {
    id: "AL-2026-0317",
    time: "15 Sep 2026, 13:48",
    type: "Suspicious Transaction",
    location: "Viman Nagar, Pune",
    description:
      "Multiple suspicious transactions detected within a short time window.",
    severity: "high",
    status: "acknowledged",
    caseId: "CC-2026-4378",
  },
  {
    id: "AL-2026-0316",
    time: "15 Sep 2026, 12:15",
    type: "ATM Risk",
    location: "Kharadi, Pune",
    description:
      "High-risk ATM cluster identified by predictive model.",
    severity: "high",
    status: "unacknowledged",
    caseId: "CC-2026-4371",
  },
  {
    id: "AL-2026-0315",
    time: "15 Sep 2026, 11:42",
    type: "Pattern Detected",
    location: "Wakad, Pune",
    description:
      "Similar complaint pattern detected across multiple cases.",
    severity: "medium",
    status: "acknowledged",
    caseId: "CC-2026-4369",
  },
  {
    id: "AL-2026-0314",
    time: "15 Sep 2026, 10:26",
    type: "Location Risk",
    location: "Aundh, Pune",
    description:
      "Increased predicted cybercrime activity detected in the area.",
    severity: "medium",
    status: "resolved",
    caseId: "CC-2026-4354",
  },
  {
    id: "AL-2026-0313",
    time: "15 Sep 2026, 09:58",
    type: "Transaction Alert",
    location: "Baner, Pune",
    description:
      "Transaction behaviour matched an existing risk pattern.",
    severity: "low",
    status: "resolved",
    caseId: "CC-2026-4348",
  },
];