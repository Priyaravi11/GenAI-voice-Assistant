type StartCallProps = {
  onStart?: () => void;
};

function StartCall({ onStart }: StartCallProps) {
  return (
    <button className="primary-button call-action" type="button" onClick={onStart}>
      ☎ Start Call
    </button>
  );
}

export default StartCall;
