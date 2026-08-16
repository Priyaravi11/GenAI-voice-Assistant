import { useState } from "react";

export function useGeminiLive() {
  const [listening, setListening] = useState(false);
  const [muted, setMuted] = useState(false);

  return {
    listening,
    muted,
    start: () => setListening(true),
    stop: () => setListening(false),
    toggleListening: () => setListening((current) => !current),
    toggleMuted: () => setMuted((current) => !current),
  };
}
