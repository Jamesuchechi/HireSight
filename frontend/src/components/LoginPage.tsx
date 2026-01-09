import React, { useState } from 'react';
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Loader2,
  Sparkles,
  CheckCircle2,
  Zap
} from 'lucide-react';
import Logo from './Logo';
import Footer from './Footer';
import type { SignInPayload } from '../types';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type SignInProps = {
  onSubmit: (data: SignInPayload) => Promise<void> | void;
  onSwitchToSignup: () => void;
  onForgotPassword: () => void;
  isLoading?: boolean;
  error?: string | null;
  statusMessage?: string | null;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function LoginPage({
  onSubmit,
  onSwitchToSignup,
  onForgotPassword,
  isLoading = false,
  error = null,
  statusMessage = null
}: SignInProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [rememberMe, setRememberMe] = useState(false);

  const handleChange = (field: 'email' | 'password') => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (touched[field]) {
      validateField(field, value);
    }
  };

  const handleBlur = (field: 'email' | 'password') => () => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    validateField(field, formData[field]);
  };

  const validateField = (field: keyof SignInPayload, value: string) => {
    setValidationErrors((prev) => {
      const errors = { ...prev };
      if (field === 'email') {
        if (!value) {
          errors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          errors.email = 'Please enter a valid email address';
        } else {
          delete errors.email;
        }
      }
      if (field === 'password') {
        if (!value) {
          errors.password = 'Password is required';
        } else {
          delete errors.password;
        }
      }
      return errors;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setTouched({ email: true, password: true });
    validateField('email', formData.email);
    validateField('password', formData.password);

    const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email);
    if (!formData.email || !formData.password || !isEmailValid) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (err) {
      // parent handles error state
    }
  };

  return (
    <div className="auth-page-shell">
      <div className="signin-page">
        <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
        
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        :root {
          --white: #FFFFFF;
          --blue: #0066FF;
          --blue-light: #E6F0FF;
          --blue-dark: #0052CC;
          --gold: #FFB800;
          --cyan: #00D4FF;
          --gray-50: #F8F9FA;
          --gray-100: #E9ECEF;
          --gray-200: #DEE2E6;
          --gray-300: #CED4DA;
          --gray-600: #6C757D;
          --gray-700: #495057;
          --gray-900: #0A0E14;
          --red: #FF3B30;
        }

        body {
          font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--white);
          color: var(--gray-900);
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        .signin-page {
          min-height: 100vh;
          display: flex;
          position: relative;
          overflow: hidden;
        }

        .auth-page-shell {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        .auth-page-shell > .signin-page {
          flex: 1;
        }

        .signin-page::before {
          content: '';
          position: absolute;
          top: -50%;
          right: -30%;
          width: 800px;
          height: 800px;
          background: radial-gradient(circle, var(--cyan) 0%, transparent 70%);
          filter: blur(120px);
          opacity: 0.3;
          animation: float 20s infinite ease-in-out;
        }

        .signin-page::after {
          content: '';
          position: absolute;
          bottom: -50%;
          left: -30%;
          width: 700px;
          height: 700px;
          background: radial-gradient(circle, var(--blue) 0%, transparent 70%);
          filter: blur(120px);
          opacity: 0.25;
          animation: float 25s infinite ease-in-out reverse;
        }

        .orb-1 {
          position: absolute;
          top: 20%;
          left: 10%;
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, var(--gold) 0%, transparent 70%);
          filter: blur(100px);
          opacity: 0.15;
          animation: float 18s infinite ease-in-out;
          animation-delay: -5s;
        }

        @keyframes float {
          0%, 100% { transform: translate(0, 0) scale(1) rotate(0deg); }
          33% { transform: translate(50px, -50px) scale(1.1) rotate(120deg); }
          66% { transform: translate(-40px, 40px) scale(0.9) rotate(240deg); }
        }

        .brand-side {
          flex: 1;
          display: flex;
          flex-direction: column;
          justify-content: center;
          padding: 4rem 6rem;
          position: relative;
          z-index: 1;
        }

        .brand-logo {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 4rem;
          animation: fadeInUp 0.8s ease forwards;
        }

        .brand-logo-icon {
          flex-shrink: 0;
        }

        .brand-logo-text {
          font-size: 2.5rem;
          font-weight: 800;
          color: var(--gray-900);
          letter-spacing: -0.02em;
          background: linear-gradient(135deg, var(--gray-900) 0%, var(--blue) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .brand-content {
          max-width: 540px;
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: 0.2s;
        }

        .brand-title {
          font-size: 3.5rem;
          font-weight: 800;
          line-height: 1.1;
          margin-bottom: 1.5rem;
          background: linear-gradient(135deg, var(--gray-900) 0%, var(--blue) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: -0.03em;
        }

        .brand-subtitle {
          font-size: 1.35rem;
          color: var(--gray-600);
          line-height: 1.7;
          margin-bottom: 3rem;
        }

        .brand-features {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 1rem;
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: calc(0.4s + var(--delay));
        }

        .feature-item:nth-child(1) { --delay: 0s; }
        .feature-item:nth-child(2) { --delay: 0.1s; }
        .feature-item:nth-child(3) { --delay: 0.2s; }

        .feature-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--blue-light);
          color: var(--blue);
          flex-shrink: 0;
        }

        .feature-text {
          font-size: 1.1rem;
          font-weight: 500;
          color: var(--gray-700);
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .form-side {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 4rem 2rem;
          position: relative;
          z-index: 1;
        }

        .form-container {
          width: 100%;
          max-width: 480px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 3rem;
          box-shadow: 0 24px 80px rgba(0, 0, 0, 0.12);
          border: 1px solid rgba(255, 255, 255, 0.8);
          animation: scaleIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .form-header {
          margin-bottom: 2.5rem;
        }

        .form-logo {
          display: flex;
          align-items: center;
          margin-bottom: 1rem;
        }

        .form-title {
          font-size: 2.25rem;
          font-weight: 700;
          color: var(--gray-900);
          margin-bottom: 0.75rem;
        }

        .form-subtitle {
          color: var(--gray-600);
          font-size: 1.05rem;
          line-height: 1.6;
        }

        .alert {
          padding: 1rem 1.25rem;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
          font-weight: 500;
          margin-bottom: 1.5rem;
          background: var(--red);
          color: white;
        }

        .status-message {
          padding: 1rem 1.25rem;
          border-radius: 12px;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
          font-weight: 500;
          margin-bottom: 1.5rem;
          background: var(--blue-light);
          color: var(--blue-dark);
        }

        .signin-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-label {
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--gray-900);
        }

        .input-wrapper {
          position: relative;
        }

        .input-icon {
          position: absolute;
          left: 1.25rem;
          top: 50%;
          transform: translateY(-50%);
          color: var(--gray-600);
          pointer-events: none;
          transition: color 0.2s ease;
        }

        .form-input {
          width: 100%;
          padding: 1rem 1.25rem 1rem 3.25rem;
          border: 2px solid var(--gray-200);
          border-radius: 14px;
          font-size: 1rem;
          font-family: 'Outfit', sans-serif;
          transition: all 0.2s ease;
          background: white;
        }

        .form-input:focus {
          outline: none;
          border-color: var(--blue);
          box-shadow: 0 0 0 4px var(--blue-light);
        }

        .form-input:focus + .input-icon {
          color: var(--blue);
        }

        .form-input.error {
          border-color: var(--red);
        }

        .form-input.error:focus {
          box-shadow: 0 0 0 4px rgba(255, 59, 48, 0.1);
        }

        .password-toggle {
          position: absolute;
          right: 1.25rem;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          color: var(--gray-600);
          padding: 0.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: color 0.2s ease;
        }

        .password-toggle:hover {
          color: var(--gray-900);
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--red);
          font-size: 0.85rem;
          font-weight: 500;
        }

        .form-options {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-top: -0.5rem;
        }

        .remember-me {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .remember-me input {
          width: 18px;
          height: 18px;
          cursor: pointer;
          accent-color: var(--blue);
        }

        .remember-me label {
          font-size: 0.9rem;
          color: var(--gray-700);
          cursor: pointer;
        }

        .forgot-password {
          color: var(--blue);
          font-weight: 600;
          font-size: 0.9rem;
          text-decoration: none;
          cursor: pointer;
          transition: color 0.2s ease;
        }

        .forgot-password:hover {
          color: var(--blue-dark);
          text-decoration: underline;
        }

        .submit-button {
          width: 100%;
          padding: 1.25rem;
          background: var(--blue);
          color: white;
          border: none;
          border-radius: 14px;
          font-weight: 600;
          font-size: 1.05rem;
          cursor: pointer;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          font-family: 'Outfit', sans-serif;
          margin-top: 1rem;
        }

        .submit-button:hover:not(:disabled) {
          background: var(--blue-dark);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 102, 255, 0.3);
        }

        .submit-button:active:not(:disabled) {
          transform: translateY(0);
        }

        .submit-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .button-loader {
          animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin: 2rem 0;
        }

        .divider-line {
          flex: 1;
          height: 1px;
          background: var(--gray-200);
        }

        .divider-text {
          color: var(--gray-600);
          font-size: 0.9rem;
          font-weight: 500;
        }

        .signup-prompt {
          text-align: center;
          font-size: 0.95rem;
          color: var(--gray-600);
        }

        .signup-link {
          color: var(--blue);
          font-weight: 600;
          text-decoration: none;
          cursor: pointer;
          transition: color 0.2s ease;
        }

        .signup-link:hover {
          color: var(--blue-dark);
          text-decoration: underline;
        }

        @media (max-width: 1024px) {
          .brand-side {
            display: none;
          }
        }

        @media (max-width: 640px) {
          .form-container {
            padding: 2rem 1.5rem;
            border-radius: 24px;
          }

          .form-title {
            font-size: 1.75rem;
          }

          .signin-page::before,
          .signin-page::after {
            width: 400px;
            height: 400px;
          }
        }
      `}</style>

        <div className="orb-1" />

        <div className="brand-side">
          <div className="brand-logo">
            <Logo showText={false} variant="default" size="medium" animated className="brand-logo-icon" />
            <div className="brand-logo-text">HireSight</div>
          </div>

          <div className="brand-content">
            <h1 className="brand-title">Welcome Back</h1>
            <p className="brand-subtitle">
              Sign in to access your dashboard and continue transforming your hiring process with
              AI-powered intelligence.
            </p>

            <div className="brand-features">
              <div className="feature-item">
                <div className="feature-icon">
                  <Zap size={24} />
                </div>
                <div className="feature-text">Pick up where you left off</div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">
                  <CheckCircle2 size={24} />
                </div>
                <div className="feature-text">Access your personalized dashboard</div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">
                  <Sparkles size={24} />
                </div>
                <div className="feature-text">Continue your hiring journey</div>
              </div>
            </div>
          </div>
        </div>

        <div className="form-side">
          <div className="form-container">
            <div className="form-header">
              <div className="form-logo">
                <Logo showText={false} size="small" animated />
              </div>
              <h2 className="form-title">Sign In</h2>
              <p className="form-subtitle">Enter your credentials to access your account</p>
            </div>

            {statusMessage && (
              <div className="status-message">
                <Sparkles size={20} />
                <span>{statusMessage}</span>
              </div>
            )}

            {error && (
              <div className="alert">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="signin-form" noValidate>
              <div className="form-group">
                <label className="form-label">Email Address</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <Mail size={20} />
                  </span>
                  <input
                    type="email"
                    className={`form-input ${touched.email && validationErrors.email ? 'error' : ''}`}
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={handleChange('email')}
                    onBlur={handleBlur('email')}
                    autoComplete="email"
                  />
                </div>
                {touched.email && validationErrors.email && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    <span>{validationErrors.email}</span>
                  </div>
                )}
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    <Lock size={20} />
                  </span>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className={`form-input ${
                      touched.password && validationErrors.password ? 'error' : ''
                    }`}
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={handleChange('password')}
                    onBlur={handleBlur('password')}
                    autoComplete="current-password"
                    style={{ paddingRight: '3.5rem' }}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {touched.password && validationErrors.password && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    <span>{validationErrors.password}</span>
                  </div>
                )}
              </div>

              <div className="form-options">
                <label className="remember-me">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={() => setRememberMe((prev) => !prev)}
                  />
                  <span>Remember me</span>
                </label>
                {onForgotPassword && (
                  <span className="forgot-password" onClick={onForgotPassword}>
                    Forgot password?
                  </span>
                )}
              </div>

              <button type="submit" className="submit-button" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 size={20} className="button-loader" />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight size={20} />
                  </>
                )}
              </button>
            </form>

            <div className="divider">
              <div className="divider-line" />
              <span className="divider-text">OR</span>
              <div className="divider-line" />
            </div>

            <div className="signup-prompt">
              Don't have an account?{' '}
              <span className="signup-link" onClick={onSwitchToSignup}>
                Create one for free
              </span>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
