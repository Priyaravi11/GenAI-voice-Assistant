const intentRows = [
  ["BILL_QUERY", "4,250", "86.5%", "1m 45s"],
  ["PLAN_CHANGE", "3,120", "92.1%", "2m 10s"],
  ["COMPLAINT", "2,180", "48.2%", "3m 40s"],
  ["NETWORK_ISSUE", "1,850", "72.4%", "2m 15s"],
  ["INTERNATIONAL_ROAMING", "1,100", "94.0%", "1m 38s"],
];

function Analytics() {
  return (
    <div className="page-stack">
      <section className="page-hero analytics-hero">
        <div>
          <p className="eyebrow">Advanced Analytics & ROI Calculator</p>
          <h1>Performance metrics, latency breakdowns, language distribution, and enterprise cost reduction analysis.</h1>
        </div>
        <div className="roi-badge">
          <span>Net Containment ROI</span>
          <strong>+95.7%</strong>
        </div>
      </section>

      <section className="roi-engine">
        <div>
          <p>Interactive ROI & Cost Reduction Engine</p>
          <h2>VoiceAI Bot vs Human Operational Cost Comparison</h2>
        </div>
        <strong className="savings">$502,500 / yr</strong>
        <label>
          Simulate Monthly Telecom Call Volume
          <span>12,500 Calls / Month</span>
          <input type="range" min="1000" max="25000" defaultValue="12500" />
        </label>
        <div className="roi-cards">
          <article><span>Human Agent Cost</span><strong>$43,750 / mo</strong></article>
          <article><span>VoiceAI GenAI Cost</span><strong>$1,875 / mo</strong></article>
          <article><span>Net Monthly OpEx Saved</span><strong>$41,875 / mo</strong></article>
        </div>
      </section>

      <section className="analytics-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>End-to-End Latency Breakdown</h2>
              <p>Execution time per processing stage</p>
            </div>
          </div>
          <div className="bar-chart">
            {[
              ["ASR", 74],
              ["NLU Intent", 24],
              ["RAG Search", 22],
              ["LLM Response", 55],
              ["TTS", 26],
            ].map(([label, value]) => (
              <div className="bar-row" key={label}>
                <span>{label}</span>
                <i style={{ width: `${value}%` }} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>Multilingual Call Volume Distribution</h2>
              <p>Customer language preference across 12.5K calls</p>
            </div>
          </div>
          <div className="donut-chart" aria-label="Language distribution" />
          <div className="donut-legend">
            <span>English 45%</span>
            <span>Hindi 30%</span>
            <span>Tamil 15%</span>
            <span>Telugu 6%</span>
            <span>Spanish 4%</span>
          </div>
        </article>

        <article className="panel wide-panel">
          <div className="panel-heading">
            <div>
              <h2>Intent Category Performance</h2>
              <p>Resolution success rate per customer query type</p>
            </div>
          </div>
          <div className="data-table compact-table">
            {intentRows.map(([intent, calls, containment, duration]) => (
              <div className="table-row" key={intent}>
                <strong>{intent}</strong>
                <span>{calls}</span>
                <em>{containment}</em>
                <span>{duration}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <div>
              <h2>CSAT Feedback Breakdown</h2>
              <p>4.4 / 5.0 average rating</p>
            </div>
          </div>
          <div className="rating-bars">
            {[60.6, 29, 7.7, 1.7, 1].map((rating, index) => (
              <div key={rating}>
                <span>{5 - index} Stars</span>
                <i><b style={{ width: `${rating}%` }} /></i>
                <strong>{rating}%</strong>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}

export default Analytics;
