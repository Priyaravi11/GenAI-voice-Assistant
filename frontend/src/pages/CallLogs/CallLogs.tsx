import type { CallRecord } from "../../types";

const records: CallRecord[] = [
  {
    id: "CALL_20260812_001234",
    customer: "ACC_88291",
    phone: "+91-98765-43210",
    language: "Hindi (hi)",
    intent: "BILL_QUERY",
    status: "Resolved",
    duration: "3m 5s",
    latency: "1720 ms avg",
    csat: 5,
  },
  {
    id: "CALL_20260812_001235",
    customer: "ACC_44102",
    phone: "+1-415-555-0192",
    language: "English (en)",
    intent: "PLAN_CHANGE",
    status: "Resolved",
    duration: "4m 0s",
    latency: "1540 ms avg",
    csat: 4,
  },
  {
    id: "CALL_20260812_001236",
    customer: "ACC_90123",
    phone: "+91-98111-22334",
    language: "Tamil (ta)",
    intent: "COMPLAINT",
    status: "Escalated",
    duration: "5m 10s",
    latency: "2210 ms avg",
    csat: 3,
  },
  {
    id: "CALL_20260812_001237",
    customer: "ACC_11209",
    phone: "+12-12-555-8833",
    language: "Spanish (es)",
    intent: "INTERNATIONAL_ROAMING",
    status: "Resolved",
    duration: "2m 0s",
    latency: "1610 ms avg",
    csat: 5,
  },
  {
    id: "CALL_20260812_001238",
    customer: "ACC_77312",
    phone: "+91-99887-11223",
    language: "Telugu (te)",
    intent: "NETWORK_ISSUE",
    status: "Failed",
    duration: "0m 45s",
    latency: "3100 ms avg",
  },
];

function CallLogs() {
  return (
    <div className="page-stack">
      <section className="page-hero logs-hero">
        <div>
          <p className="eyebrow">Conversation Audit & Call Logs</p>
          <h1>Search, review turn-by-turn transcripts, inspect confidence scores, and export audit trails.</h1>
        </div>
        <button className="primary-button" type="button">⇩ Export CSV Report</button>
      </section>

      <section className="filter-panel">
        <label>
          Search
          <input placeholder="Search phone, account, call ID..." />
        </label>
        <label>
          Status
          <select><option>All Statuses</option><option>Resolved</option><option>Escalated</option></select>
        </label>
        <label>
          Lang
          <select><option>All Languages</option><option>Hindi</option><option>English</option></select>
        </label>
        <label>
          Intent
          <select><option>All Intents</option><option>BILL_QUERY</option><option>NETWORK_ISSUE</option></select>
        </label>
        <p>Showing <strong>5 of 5</strong> indexed call records</p>
      </section>

      <section className="panel table-shell">
        <div className="logs-table">
          <div className="logs-head">
            <span>Call ID & Customer</span>
            <span>Language</span>
            <span>Intent</span>
            <span>Status</span>
            <span>Duration & Latency</span>
            <span>CSAT Rating</span>
            <span>Actions</span>
          </div>
          {records.map((record) => (
            <div className="logs-row" key={record.id}>
              <div>
                <strong>{record.id}</strong>
                <small>{record.phone}</small>
                <small>{record.customer}</small>
              </div>
              <span>{record.language}</span>
              <em>{record.intent}</em>
              <b className={`status ${record.status.toLowerCase()}`}>{record.status}</b>
              <div>
                <strong>{record.duration}</strong>
                <small>{record.latency}</small>
              </div>
              <span className="rating">{record.csat ? `★ ${record.csat} / 5` : "Unrated"}</span>
              <button type="button">View Turns →</button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default CallLogs;
