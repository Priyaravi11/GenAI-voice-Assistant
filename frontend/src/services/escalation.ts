import { apiRequest } from "./api";

export type EscalationPayload = {
  callId: string;
  reason: string;
  priority: "low" | "medium" | "high" | "critical";
};

export function createEscalation(payload: EscalationPayload) {
  return apiRequest<{ caseId: string; status: string }>("/api/escalations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
