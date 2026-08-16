type EscalationBannerProps = {
  reason: string;
};

function EscalationBanner({ reason }: EscalationBannerProps) {
  return (
    <section className="escalation-banner">
      <div>
        <span>⚡</span>
        <div>
          <strong>Human handoff recommended</strong>
          <p>{reason}</p>
        </div>
      </div>
      <button type="button">Assign Specialist</button>
    </section>
  );
}

export default EscalationBanner;
