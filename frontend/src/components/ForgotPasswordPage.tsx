import { useState } from 'react';

type Props = {
  onRequest: (email: string) => Promise<void> | void;
  onBackToLogin: () => void;
  isLoading?: boolean;
  statusMessage?: string | null;
  error?: string | null;
};

export default function ForgotPasswordPage({
  onRequest,
  onBackToLogin,
  isLoading = false,
  statusMessage,
  error
}: Props) {
  const [email, setEmail] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!email.trim()) return;
    await onRequest(email.trim());
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <h1>Reset your password</h1>
        <p className="auth-subtitle">
          Tell us the email tied to your HireSight account and we’ll send you a reset token.
        </p>
        {statusMessage && <div className="status-message">{statusMessage}</div>}
        {error && <div className="error-message">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Work email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <button type="submit" className="primary-button full-width" disabled={isLoading}>
            {isLoading ? 'Sending link...' : 'Send reset token'}
          </button>
        </form>
        <p className="text-muted auth-note">
          Remembered your password?{' '}
          <button className="link-text" onClick={onBackToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
