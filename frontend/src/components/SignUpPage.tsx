import { useMemo, useState } from 'react';
import type { SignUpPayload, AccountType } from '../types';

type Props = {
  onSubmit: (payload: SignUpPayload) => Promise<void> | void;
  onSwitchToLogin: () => void;
  isLoading?: boolean;
  error?: string | null;
};

const ACCOUNT_DISPLAY: Record<AccountType, string> = {
  personal: 'Job Seeker',
  company: 'Company'
};

export default function SignUpPage({ onSubmit, onSwitchToLogin, isLoading = false, error }: Props) {
  const [form, setForm] = useState<SignUpPayload>({
    name: '',
    email: '',
    password: '',
    account_type: 'personal'
  });

  const enabled = useMemo(() => form.name && form.email && form.password.length >= 8, [form]);

  const handleChange = (field: keyof SignUpPayload) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleAccountSwitch = (type: AccountType) => {
    setForm((prev) => ({
      ...prev,
      account_type: type
    }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!enabled) return;
    await onSubmit(form);
  };

  return (
    <div className="auth-shell">
      <div className="auth-panel">
        <h1>Create your HireSight account</h1>
        <p className="auth-subtitle">
          Launch into bias-free hiring with AI-powered parsing, semantic matching, and pipeline automation.
        </p>
        {error && <div className="error-message">{error}</div>}
        <div className="role-toggle" aria-label="Account type">
          {(Object.keys(ACCOUNT_DISPLAY) as AccountType[]).map((type) => (
            <button
              key={type}
              type="button"
              className={form.account_type === type ? 'active' : ''}
              onClick={() => handleAccountSwitch(type)}
            >
              {ACCOUNT_DISPLAY[type]}
            </button>
          ))}
        </div>
        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Full name"
            value={form.name}
            onChange={handleChange('name')}
            required
          />
          <input type="email" placeholder="Work email" value={form.email} onChange={handleChange('email')} required />
          <input
            type="password"
            placeholder="Strong password"
            value={form.password}
            onChange={handleChange('password')}
            required
            minLength={8}
          />
          <button type="submit" className="primary-button full-width" disabled={!enabled || isLoading}>
            {isLoading ? 'Creating account...' : 'Create account'}
          </button>
        </form>
        <p className="text-muted auth-note">
          Already have an account?{' '}
          <button className="link-text" onClick={onSwitchToLogin}>
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
