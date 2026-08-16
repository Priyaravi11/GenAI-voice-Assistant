import React from "react";

type LoadingProps = {
  label?: string;
};

const Loading = React.memo(function Loading({ label = "Loading VoiceAI workspace" }: LoadingProps) {
  return (
    <div className="loading-state" role="status">
      <span />
      <strong>{label}</strong>
    </div>
  );
});

export default Loading;
