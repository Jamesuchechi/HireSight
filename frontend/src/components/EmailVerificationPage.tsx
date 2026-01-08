import { useState } from 'react';

type Props = {
  email?: string | null;
  onVerify: (token: string) => Promise<void> | void;
  onBackToLogin: () => void;
  statusMessage?: string | null;
  error?: string | null;
};

export default function EmailVerificationPage({
  email,
  onVerify,
  onBackToLogin,
  statusMessage,
  error
}: Props) {
  const [token, setToken] = useState('');
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!token.trim()) return;
    await onVerify(token.trim());
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <h1>Verify your email</h1>
        <p className="auth-subtitle">
          Enter the verification token sent to{' '}
          <strong>{email ?? 'your inbox'}</strong> to activate your account.
        </p>
        {statusMessage && <div className="status-message">{statusMessage}</div>}
        {error && <div className="error-message">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Verification token"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            required
          />
          <button type="submit" className="primary-button full-width">
            Verify & Sign in
          </button>
        </form>
        <p className="text-muted auth-note">
          Already verified?{' '}
          <button className="link-text" onClick={onBackToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
