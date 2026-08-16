type VoiceButtonProps = {
  active: boolean;
  onToggle: () => void;
};

function VoiceButton({ active, onToggle }: VoiceButtonProps) {
  return (
    <button
      className={active ? "voice-button active" : "voice-button"}
      type="button"
      onClick={onToggle}
      aria-pressed={active}
    >
      <span />
      {active ? "Listening" : "Push to Talk"}
    </button>
  );
}

export default VoiceButton;
