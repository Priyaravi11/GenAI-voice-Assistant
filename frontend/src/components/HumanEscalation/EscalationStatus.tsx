type EscalationStatusProps = {
  queueDepth: number;
  sla: string;
};

function EscalationStatus({ queueDepth, sla }: EscalationStatusProps) {
  return (
    <div className="handoff-status">
      <article>
        <span>Queue Depth</span>
        <strong>{queueDepth}</strong>
      </article>
      <article>
        <span>Target SLA</span>
        <strong>{sla}</strong>
      </article>
      <article>
        <span>Routing</span>
        <strong>Skill-based</strong>
      </article>
    </div>
  );
}

export default EscalationStatus;
