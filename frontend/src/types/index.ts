export type ThemePreference = "dark" | "light" | "system";

export type AppView =
  | "dashboard"
  | "live"
  | "logs"
  | "config"
  | "analytics"
  | "agents";

export type AuthSession = {
  session_id: string;
  language: string;
  customer_id: string | null;
  status: string;
  account_id: string;
  account_status?: string | null;
  connection_status?: string | null;
};

export type CallStatus = "Resolved" | "Escalated" | "Failed" | "Monitoring";

export type TranscriptEntry = {
  id: string;
  speaker: "Customer" | "VoiceAI" | "Human Agent";
  language: string;
  text: string;
  translated?: string;
  time: string;
  confidence: number;
};

export type CallRecord = {
  id: string;
  customer: string;
  phone: string;
  language: string;
  intent: string;
  status: CallStatus;
  duration: string;
  latency: string;
  csat?: number;
};

export type Metric = {
  label: string;
  value: string;
  detail: string;
  trend: string;
};

export type Agent = {
  name: string;
  queue: string;
  status: "Available" | "On Call" | "Wrapping Up";
  score: string;
};
