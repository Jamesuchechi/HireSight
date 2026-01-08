import { useState } from 'react';

type Props = {
  onReset: (token: string, newPassword: string) => Promise<void> | void;
  onBackToLogin: () => void;
  isLoading?: boolean;
  statusMessage?: string | null;
  error?: string | null;
};

export default function ResetPasswordPage({
  onReset,
  onBackToLogin,
  isLoading = false,
  statusMessage,
  error
}: Props) {
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setLocalError('Passwords must match');
      return;
    }
    setLocalError(null);
    await onReset(token.trim(), password);
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <h1>Enter your reset token</h1>
        <p className="auth-subtitle">
          Paste the token you received and choose a new strong password.
        </p>
        {statusMessage && <div className="status-message">{statusMessage}</div>}
        {(error || localError) && (
          <div className="error-message">{localError ?? error}</div>
        )}
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Reset token"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            required
          />
          <input
            type="password"
            placeholder="New password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            required
          />
          <input
            type="password"
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            minLength={8}
            required
          />
          <button type="submit" className="primary-button full-width" disabled={isLoading}>
            {isLoading ? 'Resetting password...' : 'Reset password'}
          </button>
        </form>
        <p className="text-muted auth-note">
          Already set?{' '}
          <button className="link-text" onClick={onBackToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
