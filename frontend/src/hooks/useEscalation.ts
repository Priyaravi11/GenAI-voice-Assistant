import { useState } from "react";
import { createEscalation, type EscalationPayload } from "../services/escalation";

export function useEscalation() {
  const [loading, setLoading] = useState(false);
  const [caseId, setCaseId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function escalate(payload: EscalationPayload) {
    setLoading(true);
    setError(null);

    try {
      const response = await createEscalation(payload);
      setCaseId(response.caseId);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Escalation failed");
    } finally {
      setLoading(false);
    }
  }

  return { loading, caseId, error, escalate };
}
