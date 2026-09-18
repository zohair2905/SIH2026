import { apiGet } from "@/lib/api/common";

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  actor: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export async function getAuditLogs(): Promise<AuditLogEntry[]> {
  return (await apiGet<AuditLogEntry[]>("/api/audit-logs")) ?? [];
}