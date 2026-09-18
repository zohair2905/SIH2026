export type SeverityLevel = "critical" | "high" | "medium" | "low";

export type ConfidenceLevel = "high" | "medium" | "low";

export type CaseStatus =
  | "new"
  | "acknowledged"
  | "investigating"
  | "resolved"
  | "open"
  | "closed";

export type AlertStatus = "new" | "acknowledged" | "dismissed" | "resolved";

export type UserStatus = "Active" | "Inactive";

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
  confidence?: number;
  topFactors?: string[];
  syntheticLocationData?: boolean;
}

export interface HeatmapEvidenceFactor {
  feature: string;
  value: number;
  label: string;
}

export interface HeatmapPoint {
  atm_id: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  best_rank: number;
  observation_count: number;
  severity: SeverityLevel;
  confidence: number;
  top_factors: HeatmapEvidenceFactor[];
  area_type: string | null;
  window_start: string | null;
  window_end: string | null;
  synthetic_location_data: boolean;
}

export interface HeatmapResponse {
  case_id: string | null;
  points: HeatmapPoint[];
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

export interface CasePredictionSummary {
  prediction_id: string;
  risk_score: number;
  severity: SeverityLevel;
  top_atm_id: string | null;
  city: string | null;
  window_end: string | null;
}

export interface CaseRecord {
  case_id: string;
  transaction_id: string | null;
  title: string;
  description: string | null;
  status: CaseStatus;
  priority: SeverityLevel;
  case_type: string;
  amount: number | null;
  created_at: string;
  updated_at: string;
  prediction: CasePredictionSummary | null;
}

export interface TransactionRecord {
  transaction_id: string;
  customer_id: string | null;
  timestamp: string | null;
  account_type: string | null;
  transaction_type: string | null;
  transaction_amount: number | null;
  account_balance: number | null;
  state: string | null;
  credit_score: number | null;
  has_loan: number | null;
  kyc_status: string | null;
  channel: string | null;
}

export type NetworkNodeKind = "transaction" | "customer" | "atm";

export type NetworkRelation =
  | "belongs_to"
  | "same_customer"
  | "candidate_withdrawal_point";

export interface NetworkNode {
  id: string;
  kind: NetworkNodeKind;
  label: string;
  details: Record<string, unknown>;
  risk: SeverityLevel | null;
}

export interface NetworkLink {
  source: string;
  target: string;
  relation: NetworkRelation;
}

export interface CaseNetwork {
  case_id: string;
  semantics: string;
  nodes: NetworkNode[];
  links: NetworkLink[];
}

export interface CaseNote {
  note_id: number;
  case_id: string;
  actor: string | null;
  note: string;
  created_at: string;
}

export interface PredictionLocation {
  rank: number;
  atm_id: string;
  risk_score: number;
  risk_score_percent: number;
  confidence: number;
  severity: SeverityLevel;
  candidate_rank: number;
  latitude: number | null;
  longitude: number | null;
  city: string | null;
  area_type: string | null;
  atm_status: string | null;
  atm_density_1km: number | null;
  atm_withdrawal_count: number | null;
  atm_recent_activity: number | null;
  synthetic_location_data: boolean;
  evidence: {
    top_factors?: string[];
    driver?: string;
    heuristic?: boolean;
    [key: string]: unknown;
  };
}

export interface PredictionRun {
  prediction_id: string;
  status: string;
  case_id: string;
  transaction_id: string;
  model_name: string;
  model_version: string;
  window: { start: string; end: string };
  confidence: number;
  confidence_heuristic: string;
  generated_at: string;
  superseded_at: string | null;
  locations: PredictionLocation[];
  note: string;
}

export interface DashboardSummary {
  cases: number;
  open_cases: number;
  alerts: number;
  active_alerts: number;
  unacknowledged_alerts: number;
  predictions: number;
  average_prediction_risk: number | null;
}

export interface SeverityCounts {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface DashboardTopAtm {
  atm_id: string;
  latitude: number;
  longitude: number;
  risk_score: number;
  best_rank: number;
  observation_count: number;
  severity: SeverityLevel;
  confidence: number;
  top_factors: HeatmapEvidenceFactor[];
  area_type: string | null;
  window_start: string | null;
  window_end: string | null;
  synthetic_location_data: boolean;
}

export interface AlertRecord {
  alert_id: number;
  case_id: string;
  prediction_id: number | null;
  transaction_id: string;
  atm_id: string;
  risk_score: number;
  severity: SeverityLevel;
  status: AlertStatus;
  message: string;
  acknowledged_by: number | null;
  acknowledged_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardOverview {
  summary: DashboardSummary;
  alert_severity_distribution: SeverityCounts;
  case_risk_distribution: SeverityCounts;
  top_atms: DashboardTopAtm[];
  recent_alerts: AlertRecord[];
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