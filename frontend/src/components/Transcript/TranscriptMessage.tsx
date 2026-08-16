import type { TranscriptEntry } from "../../types";

type TranscriptMessageProps = {
  entry: TranscriptEntry;
};

function TranscriptMessage({ entry }: TranscriptMessageProps) {
  return (
    <article className={`transcript-message ${entry.speaker.toLowerCase().replace(" ", "-")}`}>
      <header>
        <strong>{entry.speaker}</strong>
        <span>{entry.language}</span>
        <time>{entry.time}</time>
      </header>
      <p>{entry.text}</p>
      {entry.translated ? <small>{entry.translated}</small> : null}
      <footer>
        <span>Confidence</span>
        <i><b style={{ width: `${entry.confidence}%` }} /></i>
        <em>{entry.confidence}%</em>
      </footer>
    </article>
  );
}

export default TranscriptMessage;
