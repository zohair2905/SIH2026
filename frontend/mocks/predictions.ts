import type {
  AccuracyDatum,
  PredictedLocation,
  RiskBarDatum,
} from "@/types";

export const riskData: RiskBarDatum[] = [
  { name: "Mon", high: 12, medium: 18, low: 9 },
  { name: "Tue", high: 15, medium: 21, low: 12 },
  { name: "Wed", high: 19, medium: 17, low: 10 },
  { name: "Thu", high: 14, medium: 24, low: 13 },
  { name: "Fri", high: 22, medium: 20, low: 11 },
  { name: "Sat", high: 17, medium: 16, low: 8 },
  { name: "Sun", high: 13, medium: 19, low: 10 },
];

export const accuracyData: AccuracyDatum[] = [
  { name: "Week 1", accuracy: 82 },
  { name: "Week 2", accuracy: 85 },
  { name: "Week 3", accuracy: 87 },
  { name: "Week 4", accuracy: 89 },
  { name: "Week 5", accuracy: 91 },
  { name: "Week 6", accuracy: 92 },
];

export const gisLocations: PredictedLocation[] = [
  {
    location: "Kharadi ATM Cluster",
    district: "Pune",
    score: "91%",
    confidence: "high",
    window: "14:00 – 18:00",
    risk: "high",
  },
  {
    location: "Hadapsar",
    district: "Pune",
    score: "84%",
    confidence: "high",
    window: "12:00 – 16:00",
    risk: "high",
  },
  {
    location: "Viman Nagar",
    district: "Pune",
    score: "76%",
    confidence: "medium",
    window: "16:00 – 20:00",
    risk: "medium",
  },
  {
    location: "Wakad",
    district: "Pune",
    score: "68%",
    confidence: "medium",
    window: "13:00 – 17:00",
    risk: "medium",
  },
  {
    location: "Shivaji Nagar",
    district: "Pune",
    score: "62%",
    confidence: "medium",
    window: "15:00 – 19:00",
    risk: "medium",
  },
];

export const latestPredictions: PredictedLocation[] = [
  {
    id: "PR-2026-092",
    location: "Kharadi ATM Cluster",
    district: "Pune",
    score: "91%",
    confidence: "high",
    window: "14:00 – 18:00",
    risk: "high",
  },
  {
    id: "PR-2026-091",
    location: "Hadapsar",
    district: "Pune",
    score: "84%",
    confidence: "high",
    window: "12:00 – 16:00",
    risk: "high",
  },
  {
    id: "PR-2026-090",
    location: "Viman Nagar",
    district: "Pune",
    score: "76%",
    confidence: "medium",
    window: "16:00 – 20:00",
    risk: "medium",
  },
  {
    id: "PR-2026-089",
    location: "Wakad",
    district: "Pune",
    score: "68%",
    confidence: "medium",
    window: "13:00 – 17:00",
    risk: "medium",
  },
  {
    id: "PR-2026-088",
    location: "Shivaji Nagar",
    district: "Pune",
    score: "62%",
    confidence: "medium",
    window: "15:00 – 19:00",
    risk: "medium",
  },
];