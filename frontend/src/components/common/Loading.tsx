type LoadingProps = {
  label?: string;
};

function Loading({ label = "Loading VoiceAI workspace" }: LoadingProps) {
  return (
    <div className="loading-state" role="status">
      <span />
      <strong>{label}</strong>
    </div>
  );
}

export default Loading;
