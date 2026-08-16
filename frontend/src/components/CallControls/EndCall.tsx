type EndCallProps = {
  onEnd?: () => void;
};

function EndCall({ onEnd }: EndCallProps) {
  return (
    <button className="danger-button call-action" type="button" onClick={onEnd}>
      End Call
    </button>
  );
}

export default EndCall;
