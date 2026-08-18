import { useCallback, useEffect, useMemo, useState } from "react";
import EndCall from "../../components/CallControls/EndCall";
import { useAudioPlayer } from "../../hooks/useAudioPlayer";
import { useAudioRecorder } from "../../hooks/useAudioRecorder";
import { useAudioWebSocket } from "../../hooks/useAudioWebSocket";
import type { AuthSession, TranscriptEntry } from "../../types";

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
  authSession?: AuthSession;
  onEndCall?: () => void;
  onOpenEscalationDesk?: () => void;
  isAdmin?: boolean;
};

function LiveCall({ authSession, onEndCall, onOpenEscalationDesk, isAdmin = false }: LiveCallProps) {
  const fallbackSessionId = useMemo(() => `session-${Date.now()}`, []);
  const sessionId = authSession?.session_id ?? fallbackSessionId;
  const customerId = authSession?.customer_id ?? undefined;
  const [language, setLanguage] = useState("English (US)");
  const [inputText, setInputText] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voiceStatus, setVoiceStatus] = useState("Idle");
  const [micError, setMicError] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>(baseTranscript);
  const player = useAudioPlayer();

  function languageCode(label: string) {
    if (label.includes("Hindi")) return "hi";
    if (label.includes("Tamil")) return "ta";
    if (label.includes("Telugu")) return "te";
    if (label.includes("Kannada")) return "kn";
    if (label.includes("Malayalam")) return "ml";
    return "en";
  }

  const addTranscript = useCallback((entry: Omit<TranscriptEntry, "id" | "time">) => {
    setTranscript((current) => [
      ...current,
      {
        ...entry,
        id: `${entry.speaker}-${Date.now()}-${current.length}`,
        time: "Now",
      },
    ]);
  }, []);

  const speakText = useCallback((text: string, lang: string) => {
    if (!("speechSynthesis" in window) || !text.trim()) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === "hi" ? "hi-IN" : lang === "ta" ? "ta-IN" : lang === "te" ? "te-IN" : lang === "kn" ? "kn-IN" : lang === "ml" ? "ml-IN" : "en-US";
    window.speechSynthesis.speak(utterance);
  }, []);

  const socket = useAudioWebSocket(sessionId, {
    onTranscript: (text) => {
      if (!text.trim()) return;
      setIsAnalyzing(true);
      addTranscript({
        speaker: "Customer",
        language: language.replace(/\s+\(.+\)/, ""),
        text,
        confidence: 90,
      });
    },
    onAssistantResponse: (message) => {
      if (message.content) {
        setIsAnalyzing(false);
        setVoiceStatus("Assistant speaking");
        const isCustomerIdPrompt = message.requires_customer_id;
        const agentLabel = message.agent ? `Agent: ${message.agent.toUpperCase()}` : "";
        const actionLabel = isCustomerIdPrompt ? "⚠️ Action required: Customer ID expected for account verification" : "";
        const note = [agentLabel, actionLabel].filter(Boolean).join(" | ");

        addTranscript({
          speaker: "VoiceAI",
          language: message.language || languageCode(language),
          text: message.content || "",
          confidence: Math.round((message.confidence ?? 0.9) * 100),
          translated: note || undefined,
        });
        speakText(message.content || "", message.language || languageCode(language));
      }
    },
    onError: (error) => {
      setMicError(error || "Something went wrong while processing the request.");
      setIsAnalyzing(false);
      setVoiceStatus("Error");
      addTranscript({
        speaker: "VoiceAI",
        language: "English",
        text: error || "Something went wrong while processing the request.",
        confidence: 0,
      });
    },
    onEscalation: (message) => {
      addTranscript({
        speaker: "VoiceAI",
        language: "English",
        text: message.reason || "This request has been marked for human escalation.",
        confidence: Math.round((message.confidence ?? 0.7) * 100),
      });
    },
    onReady: () => setVoiceStatus("Recording ready"),
    onStreamClosed: () => setVoiceStatus("Idle"),
    onStatus: (message) => {
      if (message.status === "processing") setVoiceStatus("Processing");
    },
  });

  const recorder = useAudioRecorder({
    onRecordingComplete: async (audio, mimeType) => {
      setVoiceStatus("Uploading recording");
      setIsAnalyzing(true);
      const buffer = await audio.arrayBuffer();
      socket.sendAudioRecording(buffer, mimeType);
      socket.endAudioStream();
    },
    onError: (error) => {
      const permissionMessage =
        error.name === "NotAllowedError"
          ? "Microphone access is required. Please allow microphone permission in your browser and try again."
          : error.message;
      setMicError(permissionMessage);
      setVoiceStatus("Microphone unavailable");
    },
  });

  useEffect(() => {
    if (!socket.connected) return;
    socket.startCall(languageCode(language), customerId);
  }, [customerId, language, socket.connected]);

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
    ]);
    setInputText("");

    socket.sendUserMessage(trimmed, languageCode(language), customerId);
  }

  async function startVoiceSession() {
    setMicError(null);
    setVoiceStatus("Requesting mic permission");
    socket.startAudioStream(languageCode(language), customerId);
    await recorder.startRecording();
    setVoiceStatus("Recording");
  }

  async function stopVoiceSession() {
    setVoiceStatus("Preparing recording");
    await recorder.stopRecording();
  }

  function toggleVoiceSession() {
    if (!socket.connected) {
      setMicError("Voice connection is still starting. Please try again in a moment.");
      return;
    }

    if (recorder.isRecording) {
      void stopVoiceSession();
      return;
    }

    void startVoiceSession();
  }

  function handleEndCall() {
    window.speechSynthesis?.cancel();
    player.stop();
    void recorder.stopRecording();
    socket.endAudioStream();
    socket.disconnect();
    onEndCall?.();
  }

  return (
    <div className="live-call-screen">
      <section className="live-status-strip">
        <div className="live-connection-pill">
          <span />
          {socket.connected ? `Connected - ${voiceStatus}` : "Connecting"}
        </div>

        <div className="live-strip-actions">
          <label className="live-language-pill">
            <span>US</span>
            <select value={language} onChange={(event) => setLanguage(event.target.value)}>
              <option>English (US)</option>
              <option>Hindi (hi)</option>
              <option>Tamil (ta)</option>
              <option>Telugu (te)</option>
              <option>Kannada (kn)</option>
              <option>Malayalam (ml)</option>
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
              className={recorder.isRecording ? "call-orb active" : "call-orb"}
              type="button"
              onClick={toggleVoiceSession}
              aria-pressed={recorder.isRecording}
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
                className={recorder.isRecording ? "round-control active" : "round-control"}
                type="button"
                onClick={toggleVoiceSession}
                aria-label={recorder.isRecording ? "Stop microphone" : "Start microphone"}
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
                <i key={index} style={{ transform: `scaleY(${recorder.isRecording ? 0.35 + recorder.audioLevel / 100 : 1})` }} />
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

          {micError ? <div className="error-inline">{micError}</div> : null}
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
