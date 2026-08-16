import { useEffect, useMemo, useState, lazy, Suspense } from "react";
import type { AppView, ThemePreference } from "./types";

// Lazy-loaded pages for code splitting
const Dashboard = lazy(() => import("./pages/Dashboard/Dashboard"));
const LiveCall = lazy(() => import("./pages/LiveCall/LiveCall"));
const CallLogs = lazy(() => import("./pages/CallLogs/CallLogs"));
const Analytics = lazy(() => import("./pages/Analytics/Analytics"));
const HumanAgent = lazy(() => import("./pages/HumanAgent/HumanAgent"));

// Simple loading fallback component
const PageLoader = () => (
  <div className="loading-state" style={{ minHeight: "400px" }}>
    <span style={{ display: "inline-block" }} />
    <p>Loading...</p>
  </div>
);

const navigation: Array<{
  id: AppView;
  label: string;
  caption: string;
  icon: string;
  badge?: string;
}> = [
  { id: "dashboard", label: "Dashboard Overview", caption: "Command center", icon: "▦" },
  { id: "live", label: "Live Call Simulator", caption: "Voice session", icon: "◌", badge: "Live GenAI" },
  { id: "logs", label: "Conversation & Call Logs", caption: "Audit trail", icon: "▤", badge: "12.5K" },
  { id: "config", label: "Admin & Model Config", caption: "Routing rules", icon: "☷" },
  { id: "analytics", label: "Analytics & Insights", caption: "ROI calculator", icon: "▥" },
  { id: "agents", label: "Human Agent Desk", caption: "Escalation queue", icon: "◎" },
];

function getSystemTheme() {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: light)").matches
    ? "light"
    : "dark";
}

function App() {
  const [activeView, setActiveView] = useState<AppView>("dashboard");
  const [themePreference, setThemePreference] = useState<ThemePreference>(() => {
    const saved = localStorage.getItem("voiceai-theme");
    return saved === "dark" || saved === "light" || saved === "system"
      ? saved
      : "system";
  });
  const [systemTheme, setSystemTheme] = useState(getSystemTheme);

  const effectiveTheme = themePreference === "system" ? systemTheme : themePreference;

  useEffect(() => {
    document.documentElement.dataset.theme = effectiveTheme;
    localStorage.setItem("voiceai-theme", themePreference);
  }, [effectiveTheme, themePreference]);

  useEffect(() => {
    const query = window.matchMedia("(prefers-color-scheme: light)");
    const handleChange = () => setSystemTheme(getSystemTheme());

    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);

  const page = useMemo(() => {
    if (activeView === "live") return <Suspense fallback={<PageLoader />}><LiveCall /></Suspense>;
    if (activeView === "logs") return <Suspense fallback={<PageLoader />}><CallLogs /></Suspense>;
    if (activeView === "analytics") return <Suspense fallback={<PageLoader />}><Analytics /></Suspense>;
    if (activeView === "agents") return <Suspense fallback={<PageLoader />}><HumanAgent /></Suspense>;
    if (activeView === "config") return <Suspense fallback={<PageLoader />}><HumanAgent mode="config" /></Suspense>;
    return <Suspense fallback={<PageLoader />}><Dashboard onNavigate={setActiveView} /></Suspense>;
  }, [activeView]);

  return (
    <main className="app-shell">
      <aside className="side-rail" aria-label="Core navigation">
        <div className="brand">
          <span className="brand-icon">⌁</span>
          <div>
            <strong>VoiceAI</strong>
            <small>Multilingual GenAI Customer Assistant</small>
          </div>
          <span className="version-pill">v2.0 Care</span>
        </div>

        <nav className="nav-card">
          <p className="nav-title">Core Navigation</p>
          {navigation.map((item) => (
            <button
              type="button"
              key={item.id}
              className={activeView === item.id ? "nav-link active" : "nav-link"}
              onClick={() => setActiveView(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>
                <strong>{item.label}</strong>
                <small>{item.caption}</small>
              </span>
              {item.badge ? <em>{item.badge}</em> : null}
            </button>
          ))}
        </nav>

        <section className="policy-card">
          <div className="card-title">
            <span>▣</span>
            <strong>Policy Compliance Active</strong>
          </div>
          <p>
            Gemini 2.5 Flash pipeline with RAG vector search and automated PII
            masking.
          </p>
          <div className="policy-stats">
            <span>Containment <strong>68.4%</strong></span>
            <span>CSAT <strong>4.4/5</strong></span>
          </div>
        </section>

        <footer className="tenant-card">
          <span>AP</span>
          <div>
            <strong>Apex Telecom</strong>
            <small>Enterprise Operations</small>
          </div>
        </footer>
      </aside>

      <section className="app-main">
        <header className="global-topbar">
          <div className="engine-pill">
            <span />
            Gemini 2.5 Flash Engine: Operational
            <small>(1.8s avg)</small>
          </div>
          <div className="topbar-actions">
            <select aria-label="Global language">
              <option>English (US)</option>
              <option>Hindi (hi)</option>
              <option>Tamil (ta)</option>
              <option>Telugu (te)</option>
              <option>Spanish (es)</option>
            </select>
            <button type="button" className="icon-button" aria-label="Refresh">
              ↻
            </button>
            <button
              type="button"
              className="primary-button"
              onClick={() => setActiveView("live")}
            >
              ☎ Start Call
            </button>
            <div className="theme-toggle" aria-label="Theme preference">
              {(["dark", "light", "system"] as ThemePreference[]).map((theme) => (
                <button
                  type="button"
                  key={theme}
                  className={themePreference === theme ? "active" : ""}
                  onClick={() => setThemePreference(theme)}
                >
                  {theme}
                </button>
              ))}
            </div>
          </div>
        </header>
        {page}
      </section>
    </main>
  );
}

export default App;
