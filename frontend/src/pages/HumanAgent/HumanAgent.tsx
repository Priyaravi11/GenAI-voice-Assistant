import AgentStatus from "../../components/AgentStatus/AgentStatus";
import EscalationStatus from "../../components/HumanEscalation/EscalationStatus";
import type { Agent } from "../../types";

const agents: Agent[] = [
  { name: "Maya Rao", queue: "Billing disputes", status: "Available", score: "98%" },
  { name: "Arjun Mehta", queue: "Network support", status: "On Call", score: "94%" },
  { name: "Nisha Iyer", queue: "Plan changes", status: "Wrapping Up", score: "96%" },
];

type HumanAgentProps = {
  mode?: "config";
};

function HumanAgent({ mode }: HumanAgentProps) {
  const isConfig = mode === "config";

  return (
    <div className="page-stack">
      <section className="page-hero">
        <div>
          <p className="eyebrow">{isConfig ? "Admin & Model Config" : "Human Agent Desk"}</p>
          <h1>
            {isConfig
              ? "Tune orchestration, model routing, safety thresholds, and escalation policies."
              : "Manage escalations, agent availability, and customer context handoff."}
          </h1>
        </div>
      </section>

      <EscalationStatus queueDepth={7} sla="02:00" />

      <section className="agent-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{isConfig ? "Model Routing Matrix" : "Available Specialists"}</h2>
              <p>{isConfig ? "Runtime policy per workload" : "Skill-based routing readiness"}</p>
            </div>
          </div>
          {isConfig ? (
            <div className="config-list">
              {[
                ["Billing query", "Gemini 2.5 Flash", "RAG required"],
                ["Complaint", "Gemini 2.5 Pro", "Escalate below 72%"],
                ["Network issue", "Flash + diagnostics", "Tool call required"],
                ["Payment retry", "Flash", "PCI masked"],
              ].map(([intent, model, rule]) => (
                <article key={intent}>
                  <strong>{intent}</strong>
                  <span>{model}</span>
                  <em>{rule}</em>
                </article>
              ))}
            </div>
          ) : (
            <AgentStatus agents={agents} />
          )}
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>{isConfig ? "Safety Controls" : "Escalation Queue"}</h2>
              <p>{isConfig ? "Guardrails applied before response delivery" : "Priority ordered customer handoffs"}</p>
            </div>
          </div>
          <div className="queue-list">
            {[
              ["Billing dispute", "Hindi", "High", "00:38"],
              ["Network outage", "Tamil", "Critical", "01:12"],
              ["Roaming refund", "Spanish", "Medium", "03:20"],
            ].map(([issue, language, priority, wait]) => (
              <article key={issue}>
                <div>
                  <strong>{issue}</strong>
                  <span>{language}</span>
                </div>
                <em>{priority}</em>
                <small>{wait}</small>
              </article>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

export default HumanAgent;
