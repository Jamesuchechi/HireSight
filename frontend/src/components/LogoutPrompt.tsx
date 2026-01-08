type Props = {
  onConfirm: () => void;
  onCancel: () => void;
};

export default function LogoutPrompt({ onConfirm, onCancel }: Props) {
  return (
    <div className="auth-shell">
      <div className="auth-panel logout">
        <h1>Leaving already?</h1>
        <p className="auth-subtitle">
          We’ll save your progress. Tap “Yes, log me out” when you’re ready to return.
        </p>
        <div className="auth-actions">
          <button className="primary-button" onClick={onConfirm}>
            Yes, log me out
          </button>
          <button className="outline-button" onClick={onCancel}>
            Go back
          </button>
        </div>
      </div>
    </div>
  );
}
