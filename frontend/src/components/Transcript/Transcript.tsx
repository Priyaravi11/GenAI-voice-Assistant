import React from "react";
import type { TranscriptEntry } from "../../types";
import TranscriptMessage from "./TranscriptMessage";

type TranscriptProps = {
  entries: TranscriptEntry[];
};

const Transcript = React.memo(function Transcript({ entries }: TranscriptProps) {
  return (
    <section className="panel transcript-panel">
      <div className="panel-heading">
        <div>
          <h2>Live Transcript</h2>
          <p>Turn-by-turn multilingual audit with confidence scores</p>
        </div>
        <span className="status-pill">Auto translated</span>
      </div>
      <div className="transcript-list">
        {entries.map((entry) => (
          <TranscriptMessage entry={entry} key={entry.id} />
        ))}
      </div>
    </section>
  );
});

export default Transcript;
