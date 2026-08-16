import type { AppView, Metric } from "../../types";

const metrics: Metric[] = [
  {
    label: "Containment Rate",
    value: "68.4%",
    detail: "8,550 calls self-served without handoff",
    trend: "+5.2% vs last week",
  },
  {
    label: "Avg Latency",
    value: "1.82s",
    detail: "Includes ASR, NLU, RAG, LLM and TTS",
    trend: "-210ms vs last week",
  },
  {
    label: "Monthly Calls",
    value: "12.5K",
    detail: "416 daily average interactions",
    trend: "+8.4% volume growth",
  },
  {
    label: "Customer Satisfaction",
    value: "4.4 / 5.0",
    detail: "Based on 2,340 post-call surveys",
    trend: "+0.15 rating boost",
  },
];

const alertCards = [
  ["Warning", "High Latency Spike", "Whisper ASR pipeline experienced 2.3s latency spike between 10:15 AM and 10:30 AM."],
  ["Error", "LLM Rate Threshold Warning", "Fallback engine reached 88% token quota limit. Switch over to Gemini 2.5 Flash operational."],
  ["Info", "New Policy Indexed", "International Data Roaming Policy v3.1 indexed in Pinecone vector DB."],
];

type DashboardProps = {
  onNavigate: (view: AppView) => void;
};

function Dashboard({ onNavigate }: DashboardProps) {
  return (
    <div className="page-stack">
      <section className="page-hero compact-hero">
        <div>
          <p className="eyebrow">VoiceAI Care Command Center</p>
          <h1>Real-time telemetry, AI containment, and automated handoff routing.</h1>
        </div>
        <div className="segmented-control" aria-label="Time horizon">
          <button className="active" type="button">24h</button>
          <button type="button">7d</button>
          <button type="button">30d</button>
        </div>
      </section>

      <section className="metric-grid">
        {metrics.map((metric) => (
          <article className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
            <em>↗ {metric.trend}</em>
            <p>{metric.detail}</p>
          </article>
        ))}
      </section>

      <section className="dashboard-grid">
        <article className="panel chart-panel wide-panel">
          <div className="panel-heading">
            <div>
              <h2>Call Volume & Handoff Telemetry</h2>
              <p>Hourly breakdown comparing AI resolved vs human escalated calls</p>
            </div>
            <div className="legend">
              <span className="dot primary" /> Total Calls
              <span className="dot neutral" /> AI Resolved
              <span className="dot soft" /> Escalated
            </div>
          </div>
          <div className="area-chart" aria-hidden="true">
            <svg viewBox="0 0 720 280" role="img">
              <defs>
                <linearGradient id="totalFill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stopColor="var(--chart-a)" stopOpacity="0.5" />
                  <stop offset="100%" stopColor="var(--chart-a)" stopOpacity="0.02" />
                </linearGradient>
              </defs>
              <path className="grid-line" d="M0 55 H720 M0 110 H720 M0 165 H720 M0 220 H720" />
              <path className="area-fill" d="M0 240 C90 265 150 250 205 210 C280 150 290 55 392 48 C480 42 575 90 720 172 L720 280 L0 280 Z" />
              <path className="line-main" d="M0 240 C90 265 150 250 205 210 C280 150 290 55 392 48 C480 42 575 90 720 172" />
              <path className="line-secondary" d="M0 238 C95 252 165 238 220 196 C295 138 315 93 410 92 C500 92 590 130 720 198" />
              <path className="line-soft" d="M0 252 C100 262 175 250 245 225 C330 195 405 188 490 206 C580 224 650 238 720 248" />
            </svg>
          </div>
          <footer className="panel-footer">
            <span>Peak Volume Window: <strong>12:00 PM - 03:00 PM</strong></span>
            <button type="button" onClick={() => onNavigate("analytics")}>View Deep Analytics →</button>
          </footer>
        </article>

        <article className="panel test-panel">
          <div className="panel-heading">
            <div>
              <h2>Test Multilingual Voice AI</h2>
              <p>Click a scenario to test real-time speech recognition and response generation.</p>
            </div>
          </div>
          {[
            ["Billing Charge Dispute", "Hindi", "मेरा बिल इतना ज्यादा क्यों आया..."],
            ["Family Plan Upgrade", "English", "I want to add a 5th mobile line..."],
            ["Broadband Outage Complaint", "Tamil", "எனக்கு WiFi வேலை செய்யவில்லை..."],
            ["Mexico Roaming Pass", "Spanish", "Como puedo activar el pase de..."],
          ].map(([title, language, sample]) => (
            <button className="scenario-card" key={title} type="button">
              <strong>{title}</strong>
              <span>{language}</span>
              <small>{sample}</small>
            </button>
          ))}
          <button className="primary-button full-width" type="button" onClick={() => onNavigate("live")}>
            Open Interactive Studio
          </button>
        </article>
      </section>

      <section className="panel health-panel">
        <div className="panel-heading">
          <div>
            <h2>Real-time Health & Alert Stream</h2>
            <p>Auto-refreshing operational log</p>
          </div>
        </div>
        <div className="alert-grid">
          {alertCards.map(([type, title, copy]) => (
            <article className={`alert-card ${type.toLowerCase()}`} key={title}>
              <span>{type}</span>
              <strong>{title}</strong>
              <p>{copy}</p>
              <button type="button">Inspect Details →</button>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

export default Dashboard;
