import Transcript from "../../components/Transcript/Transcript";
import type { TranscriptEntry } from "../../types";

const entries: TranscriptEntry[] = [
  {
    id: "d1",
    speaker: "Customer",
    language: "English",
    text: "I need to understand why my roaming pack renewed twice.",
    time: "02:18",
    confidence: 96,
  },
  {
    id: "d2",
    speaker: "VoiceAI",
    language: "English",
    text: "I found duplicate renewal attempts and created a refund review note.",
    time: "02:24",
    confidence: 93,
  },
];

function CallDetails() {
  return (
    <div className="page-stack">
      <section className="page-hero">
        <div>
          <p className="eyebrow">Call Detail</p>
          <h1>Transcript, tool calls, compliance notes, and handoff context.</h1>
        </div>
      </section>
      <Transcript entries={entries} />
    </div>
  );
}

export default CallDetails;
