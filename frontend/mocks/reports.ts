import type { CaseCategoryDatum, Report } from "@/types";

export const initialReports: Report[] = [
  {
    id: "RPT-2026-0915",
    name: "Daily Cybercrime Risk Report",
    type: "Risk Analysis",
    generated: "15 Sep 2026, 14:30",
    generatedBy: "Admin Officer",
    status: "Ready",
  },
  {
    id: "RPT-2026-0914",
    name: "Cash Withdrawal Prediction Report",
    type: "Prediction",
    generated: "14 Sep 2026, 18:15",
    generatedBy: "Insp. A. Patil",
    status: "Ready",
  },
  {
    id: "RPT-2026-0913",
    name: "High Risk Location Report",
    type: "GIS Intelligence",
    generated: "13 Sep 2026, 16:45",
    generatedBy: "PSI R. Singh",
    status: "Ready",
  },
];

export const reportChartData: CaseCategoryDatum[] = [
  { name: "UPI", cases: 42 },
  { name: "Banking", cases: 31 },
  { name: "Investment", cases: 24 },
  { name: "Phishing", cases: 18 },
  { name: "Card", cases: 15 },
];