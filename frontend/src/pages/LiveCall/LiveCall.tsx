import { useState } from "react";
import EndCall from "../../components/CallControls/EndCall";
import { useGeminiLive } from "../../hooks/useGeminiLive";
import type { TranscriptEntry } from "../../types";

const presetQueries = [
  ["Bill Inquiry", "What is my current bill and due date?"],
  ["Bill Dispute", "Why is my bill higher this month?"],
  ["Outage Report", "My internet keeps dropping since yesterday evening."],
  ["5G Setup", "How do I activate 5G Standalone on my phone?"],
  ["Human Agent", "I want to speak with a human support agent."],
  ["Hindi Billing", "Mera is mahine ka bill kitna hai?"],
];

const baseTranscript: TranscriptEntry[] = [
  {
    id: "core-1",
    speaker: "VoiceAI",
    language: "English",
    text: "Hello Priya, VoiceAI Core connected. How can I assist you with your broadband or mobile service today?",
    time: "00:12",
    confidence: 98,
  },
];

type LiveCallProps = {
  onEndCall?: () => void;
  onOpenEscalationDesk?: () => void;
  isAdmin?: boolean;
};

function LiveCall({ onEndCall, onOpenEscalationDesk, isAdmin = false }: LiveCallProps) {
  const [language, setLanguage] = useState("English (US)");
  const [inputText, setInputText] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>(baseTranscript);
  const live = useGeminiLive();

  function detectLanguage(text: string) {
    if (/[\u0900-\u097F]/.test(text)) return "Hindi";
    if (/[\u0B80-\u0BFF]/.test(text)) return "Tamil";
    if (/[\u0C00-\u0C7F]/.test(text)) return "Telugu";
    if (text.toLowerCase().includes("hola") || text.toLowerCase().includes("roaming")) return "Spanish";
    return language.replace(/\s+\(.+\)/, "");
  }

  function handleSendQuery(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    const detected = detectLanguage(trimmed);
    setIsAnalyzing(true);
    setTranscript((current) => [
      ...current,
      {
        id: `u-${Date.now()}`,
        speaker: "Customer",
        language: detected,
        text: trimmed,
        time: "Now",
        confidence: 92,
      },
      {
        id: `a-${Date.now()}`,
        speaker: "VoiceAI",
        language: "English",
        text: "I am checking the account context, matching policy, and available telecom tools for this request.",
        time: "Now",
        confidence: 95,
      },
    ]);
    setInputText("");

    window.setTimeout(() => setIsAnalyzing(false), 650);
  }

  function handleEndCall() {
    live.stop();
    onEndCall?.();
  }

  return (
    <div className="live-call-screen">
      <section className="live-status-strip">
        <div className="live-connection-pill">
          <span />
          Connected - Real-time Analysis Active
        </div>

        <div className="live-strip-actions">
          <label className="live-language-pill">
            <span>US</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option>English (US)</option>
              <option>Hindi (hi)</option>
              <option>Tamil (ta)</option>
              <option>Telugu (te)</option>
              <option>Spanish (es)</option>
            </select>
          </label>
          <div className="detecting-pill">
            <span />
            Detecting: {language}
          </div>
        </div>
      </section>

      <section className="live-call-grid">
        <div className="call-studio-panel">
          <div className="preset-chip-row">
            {presetQueries.map(([label, query]) => (
              <button type="button" key={label} onClick={() => handleSendQuery(query)}>
                <span>{label === "5G Setup" ? "5G" : label.slice(0, 2).toUpperCase()}</span>
                <strong>{label}</strong>
              </button>
            ))}
          </div>

          <div className="live-orb-zone" aria-label="Voice call activity">
            {isPaused ? <div className="hold-banner">Call is currently on hold</div> : null}
            <button
              className={live.listening ? "call-orb active" : "call-orb"}
              type="button"
              onClick={live.toggleListening}
              aria-pressed={live.listening}
            >
              <span className="orb-shadow" />
              <span className="orb-bars" aria-hidden="true">
                {Array.from({ length: 7 }, (_, index) => (
                  <i key={index} />
                ))}
              </span>
            </button>
          </div>

          <div className="live-composer">
            <input
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") handleSendQuery(inputText);
              }}
              placeholder="Speak via mic or type a telecom inquiry..."
            />
            <button type="button" aria-label="Send message" onClick={() => handleSendQuery(inputText)} disabled={!inputText.trim()}>
              Send
            </button>
          </div>

          <footer className="live-control-bar">
            <div className="left-call-controls">
              <button
                className={live.listening ? "round-control active" : "round-control"}
                type="button"
                onClick={live.toggleListening}
                aria-label={live.listening ? "Mute microphone" : "Start microphone"}
              >
                Mic
              </button>
              <button
                className={isPaused ? "round-control active" : "round-control"}
                type="button"
                onClick={() => setIsPaused((current) => !current)}
                aria-label={isPaused ? "Resume call" : "Hold call"}
              >
                {isPaused ? "Play" : "Hold"}
              </button>
            </div>

            <div className="mini-wave" aria-hidden="true">
              {Array.from({ length: 12 }, (_, index) => (
                <i key={index} />
              ))}
            </div>

            <EndCall onEnd={handleEndCall} />
          </footer>

          {isAnalyzing ? (
            <div className="analysis-toast">
              <span />
              <div>
                <strong>Analyzing customer intent</strong>
                <p>Checking language, RAG match, and next best action.</p>
              </div>
            </div>
          ) : null}
        </div>

        <aside className="transcription-panel">
          <header>
            <h2><span /> Live Transcription</h2>
            <small>{transcript.length} utterances</small>
          </header>
          <div className="transcription-list">
            {transcript.map((entry) => (
              <article className="transcription-message" key={entry.id}>
                <div className="message-meta">
                  <strong>{entry.speaker === "VoiceAI" ? "VOICEAI CORE" : entry.speaker.toUpperCase()}</strong>
                  <time>{entry.time}</time>
                </div>
                <p>{entry.text}</p>
                {entry.translated ? <small>{entry.translated}</small> : null}
              </article>
            ))}
          </div>

          {isAdmin && onOpenEscalationDesk ? (
            <button className="primary-button transcription-action" type="button" onClick={onOpenEscalationDesk}>
              Open Escalation Desk
            </button>
          ) : null}
        </aside>
      </section>
    </div>
  );
}

export default LiveCall;
