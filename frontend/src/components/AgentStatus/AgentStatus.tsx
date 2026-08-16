import type { Agent } from "../../types";

type AgentStatusProps = {
  agents: Agent[];
};

function AgentStatus({ agents }: AgentStatusProps) {
  return (
    <div className="agent-list">
      {agents.map((agent) => (
        <article className="agent-card" key={agent.name}>
          <div>
            <strong>{agent.name}</strong>
            <span>{agent.queue}</span>
          </div>
          <em className={`agent-state ${agent.status.toLowerCase().replace(/\s+/g, "-")}`}>
            {agent.status}
          </em>
          <small>QA score {agent.score}</small>
        </article>
      ))}
    </div>
  );
}

export default AgentStatus;
