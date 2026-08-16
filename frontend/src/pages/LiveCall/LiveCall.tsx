import { useState } from "react";
import EndCall from "../../components/CallControls/EndCall";
import StartCall from "../../components/CallControls/StartCall";
import EscalationBanner from "../../components/HumanEscalation/EscalationBanner";
import AgentConnecting from "../../components/HumanEscalation/AgentConnecting";
import LanguageSelector from "../../components/LanguageSelector/LanguageSelector";
import Transcript from "../../components/Transcript/Transcript";
import VoiceInterface from "../../components/VoiceInterface/VoiceInterface";
import type { TranscriptEntry } from "../../types";

const transcript: TranscriptEntry[] = [
  {
    id: "t1",
    speaker: "Customer",
    language: "Hindi",
    text: "मेरा बिल इस महीने बहुत ज्यादा आया है.",
    translated: "My bill is very high this month.",
    time: "04:11",
    confidence: 94,
  },
  {
    id: "t2",
    speaker: "VoiceAI",
    language: "English",
    text: "I found two roaming add-ons added on August 12. I can explain or reverse eligible charges.",
    time: "04:12",
    confidence: 97,
  },
  {
    id: "t3",
    speaker: "Customer",
    language: "Hindi",
    text: "अगर charge गलत है तो कृपया agent से connect कर दीजिए.",
    translated: "If the charge is incorrect, please connect me with an agent.",
    time: "04:13",
    confidence: 91,
  },
];

function LiveCall() {
  const [active, setActive] = useState(true);
  const [language, setLanguage] = useState("Hindi (hi)");

  return (
    <div className="page-stack">
      <section className="page-hero live-hero">
        <div>
          <p className="eyebrow">Live Call Simulator</p>
          <h1>Operate a multilingual customer call with transcript, tools, and human handoff in one view.</h1>
        </div>
        <div className="call-controls">
          <StartCall onStart={() => setActive(true)} />
          <EndCall onEnd={() => setActive(false)} />
        </div>
      </section>

      <section className="live-layout">
        <div className="live-main">
          <VoiceInterface
            active={active}
            language={language}
            onToggle={() => setActive((current) => !current)}
          />
          <EscalationBanner reason="Low billing confidence and repeated dispute language detected." />
          <Transcript entries={transcript} />
        </div>

        <aside className="live-aside">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Session Controls</h2>
                <p>Runtime configuration for the current call</p>
              </div>
            </div>
            <LanguageSelector value={language} onChange={setLanguage} />
            <div className="tool-list">
              {["Billing lookup", "Plan recommender", "Network diagnostics", "Payment retry"].map((tool) => (
                <button type="button" key={tool}>{tool}</button>
              ))}
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>AI Decision Trace</h2>
                <p>Grounding and routing signals</p>
              </div>
            </div>
            <div className="trace-list">
              <span><strong>Intent</strong> BILL_QUERY</span>
              <span><strong>Sentiment</strong> Frustrated</span>
              <span><strong>RAG Match</strong> Billing Policy v4.2</span>
              <span><strong>Next Best Action</strong> Agent handoff</span>
            </div>
          </section>

          <AgentConnecting />
        </aside>
      </section>
    </div>
  );
}

export default LiveCall;
