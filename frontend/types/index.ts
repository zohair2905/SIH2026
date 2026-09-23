export type SeverityLevel = "high" | "medium" | "low";

export type ConfidenceLevel = "high" | "medium" | "low";

export type CaseStatus =
  | "new"
  | "acknowledged"
  | "investigating"
  | "resolved";

export type AlertStatus = "unacknowledged" | "acknowledged" | "resolved";

export type UserStatus = "Active" | "Inactive";

export interface CaseSummary {
  id: string;
  date: string;
  type: string;
  location: string;
  amount: string;
  risk: SeverityLevel;
  score: string;
  status: CaseStatus;
  officer: string;
}

export interface PredictedLocation {
  number?: number;
  id?: string;
  location: string;
  district: string;
  score: string;
  confidence: ConfidenceLevel;
  window: string;
  risk: SeverityLevel;
}

export interface RecentAlert {
  time: string;
  caseId: string;
  location: string;
  type: string;
  severity: SeverityLevel;
  status: CaseStatus;
  assigned: string;
}

export interface AlertSummary {
  id: string;
  time: string;
  type: string;
  location: string;
  description: string;
  severity: SeverityLevel;
  status: AlertStatus;
  caseId: string;
}

export interface Report {
  id: string;
  name: string;
  type: string;
  generated: string;
  generatedBy: string;
  status: "Ready";
}

export interface PlatformUser {
  id: number;
  name: string;
  role: string;
  department: string;
  email: string;
  status: UserStatus;
  lastLogin: string;
}

export interface AuditLog {
  id: string;
  date: string;
  user: string;
  action: string;
  target: string;
  status: "Success" | "Failed";
  ip: string;
}

export interface GisLocation {
  name: string;
  area: string;
  score: number;
  risk: SeverityLevel;
  cases: number;
  window: string;
  position: [number, number];
}

export interface RiskBarDatum {
  name: string;
  high: number;
  medium: number;
  low: number;
}

export interface AccuracyDatum {
  name: string;
  accuracy: number;
}

export interface CaseCategoryDatum {
  name: string;
  cases: number;
}

export interface DashboardKPIs {
  totalCases: number;
  highRiskCases: number;
  activeAlerts: number;
  predictionsToday: number;
}

export interface CaseTransaction {
  id: string;
  date: string;
  bank: string;
  channel: string;
  amount: string;
  status: string;
}

export interface NetworkNode {
  id: string;
  role: string;
  risk: SeverityLevel;
}

export interface NetworkLink {
  source: string;
  target: string;
}

export interface CaseNetwork {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

export interface DashboardOverview {
  kpis: DashboardKPIs;
  predictedLocations: PredictedLocation[];
  recentAlerts: RecentAlert[];
}

export interface PredictionRunInput {
  crimeTypes: string[];
  districts: string[];
  window: string;
}

export interface PredictionResult {
  id: string;
  status: "queued" | "processing" | "completed" | "failed";
  generatedAt: string;
  locations: PredictedLocation[];
}