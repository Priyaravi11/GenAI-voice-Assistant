import React from "react";
import VoiceButton from "./VoiceButton";

type VoiceInterfaceProps = {
  active: boolean;
  language: string;
  onToggle: () => void;
};

const VoiceInterface = React.memo(function VoiceInterface({ active, language, onToggle }: VoiceInterfaceProps) {
  return (
    <section className="voice-console">
      <div className="voice-stage">
        <div className={active ? "voice-core active" : "voice-core"}>
          <span>AI</span>
        </div>
        <div className="voice-wave" aria-hidden="true">
          {Array.from({ length: 28 }, (_, index) => (
            <i key={index} />
          ))}
        </div>
      </div>
      <div className="voice-meta">
        <p className="eyebrow">Gemini Live Session</p>
        <h2>{language} conversation stream</h2>
        <p>
          Real-time ASR, multilingual intent detection, RAG grounding, and
          tool execution are active for this simulated customer call.
        </p>
        <VoiceButton active={active} onToggle={onToggle} />
      </div>
    </section>
  );
});

export default VoiceInterface;
