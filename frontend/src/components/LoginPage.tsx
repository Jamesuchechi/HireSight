import { useState } from 'react';
import type { SignInPayload } from '../types';

type Props = {
  isLoading?: boolean;
  error?: string | null;
  onSubmit: (payload: SignInPayload) => Promise<void> | void;
  onSwitchToSignup: () => void;
  onForgotPassword: () => void;
  statusMessage?: string | null;
};

export default function LoginPage({
  isLoading = false,
  error,
  onSubmit,
  onSwitchToSignup,
  onForgotPassword,
  statusMessage
}: Props) {
  const [form, setForm] = useState<SignInPayload>({ email: '', password: '' });

  const handleChange =
    (field: keyof SignInPayload) => (event: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: event.target.value }));
    };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    await onSubmit(form);
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <h1>Welcome back</h1>
        <p className="auth-subtitle">
          Sign in to continue where you left off and let HireSight streamline your hiring journey.
        </p>
        {statusMessage && <div className="status-message">{statusMessage}</div>}
        {error && <div className="error-message">{error}</div>}
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email address"
            value={form.email}
            onChange={handleChange('email')}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={handleChange('password')}
            required
            minLength={8}
          />
          <button type="submit" className="primary-button full-width" disabled={isLoading}>
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        <div className="text-muted auth-note">
          Don’t have an account?{' '}
          <button type="button" className="link-text" onClick={onSwitchToSignup}>
            Sign up
          </button>
        </div>
        <div className="text-muted">
          Forgot your password?{' '}
          <button type="button" className="link-text" onClick={onForgotPassword}>
            Reset it
          </button>
        </div>
      </div>
    </div>
  );
}
