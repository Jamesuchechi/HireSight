import React, { useEffect, useState } from 'react';
import {
  Mail,
  Lock,
  User,
  Building2,
  Eye,
  EyeOff,
  ArrowRight,
  AlertCircle,
  Loader2,
  CheckCircle2,
  UserCircle2,
  Sparkles,
  Target,
  Shield
} from 'lucide-react';
import Logo from './Logo';
import Footer from './Footer';
import type { AccountType, SignUpPayload } from '../types';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type SignUpProps = {
  onSubmit: (data: SignUpPayload) => Promise<void> | void;
  onSwitchToLogin: () => void;
  isLoading?: boolean;
  error?: string | null;
};

// ============================================================================
// PASSWORD STRENGTH CHECKER
// ============================================================================

const calculatePasswordStrength = (password: string): number => {
  let strength = 0;
  if (password.length >= 8) strength += 25;
  if (password.length >= 12) strength += 10;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 20;
  if (/\d/.test(password)) strength += 20;
  if (/[^a-zA-Z0-9]/.test(password)) strength += 25;
  return Math.min(strength, 100);
};

const getPasswordStrengthLabel = (strength: number): { label: string; color: string } => {
  if (strength < 30) return { label: 'Weak', color: '#FF3B30' };
  if (strength < 60) return { label: 'Fair', color: '#FF9500' };
  if (strength < 85) return { label: 'Good', color: '#00C853' };
  return { label: 'Strong', color: '#0066FF' };
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function SignUpPage({
  onSubmit,
  onSwitchToLogin,
  isLoading = false,
  error = null
}: SignUpProps) {
  const [accountType, setAccountType] = useState<AccountType>('personal');
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    companyName: ''
  });
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [passwordStrength, setPasswordStrength] = useState(0);

  useEffect(() => {
    setPasswordStrength(calculatePasswordStrength(formData.password));
  }, [formData.password]);

  const handleChange =
    (field: 'email' | 'password' | 'name' | 'companyName') =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value;
      setFormData((prev) => ({ ...prev, [field]: value }));
      if (touched[field]) {
        validateField(field, value);
      }
    };

  const handleBlur = (field: 'email' | 'password' | 'name' | 'companyName') => () => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    validateField(field, formData[field]);
  };

  const validateField = (field: keyof typeof formData, value: string) => {
    setValidationErrors((prev) => {
      const errors = { ...prev };
      switch (field) {
        case 'email':
          if (!value) {
            errors.email = 'Email is required';
          } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            errors.email = 'Please enter a valid email address';
          } else {
            delete errors.email;
          }
          break;
        case 'password':
          if (!value) {
            errors.password = 'Password is required';
          } else if (value.length < 8) {
            errors.password = 'Password must be at least 8 characters';
          } else if (!/(?=.*[a-z])(?=.*[A-Z])/.test(value)) {
            errors.password = 'Password must contain uppercase and lowercase letters';
          } else if (!/(?=.*\d)/.test(value)) {
            errors.password = 'Password must contain at least one number';
          } else if (!/(?=.*[^a-zA-Z0-9])/.test(value)) {
            errors.password = 'Password must contain at least one special character';
          } else {
            delete errors.password;
          }
          break;
        case 'name':
          if (accountType === 'personal' && !value) {
            errors.name = 'Name is required';
          } else {
            delete errors.name;
          }
          break;
        case 'companyName':
          if (accountType === 'company' && !value) {
            errors.companyName = 'Company name is required';
          } else {
            delete errors.companyName;
          }
          break;
      }
      return errors;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const fieldsToValidate: Array<'email' | 'password' | 'name' | 'companyName'> = [
      'email',
      'password',
      accountType === 'personal' ? 'name' : 'companyName'
    ];

    fieldsToValidate.forEach((field) => {
      setTouched((prev) => ({ ...prev, [field]: true }));
      validateField(field, formData[field]);
    });

    const nameOrCompanyValue = accountType === 'personal' ? formData.name : formData.companyName;

    const isEmailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email);
    const hasUpperLower = /(?=.*[a-z])(?=.*[A-Z])/.test(formData.password);
    const hasNumber = /(?=.*\d)/.test(formData.password);
    const hasSpecial = /(?=.*[^a-zA-Z0-9])/.test(formData.password);

    if (
      !formData.email ||
      !formData.password ||
      !nameOrCompanyValue ||
      !isEmailValid ||
      formData.password.length < 8 ||
      !hasUpperLower ||
      !hasNumber ||
      !hasSpecial
    ) {
      return;
    }

    const signUpData: SignUpPayload = {
      email: formData.email,
      password: formData.password,
      account_type: accountType,
      name:
        accountType === 'personal'
          ? formData.name
          : formData.companyName || formData.name || 'HireSight partner',
      ...(accountType === 'company'
        ? { company_name: formData.companyName }
        : {})
    };

    try {
      await onSubmit(signUpData);
    } catch (err) {
      // parent handles error state
    }
  };

  const strengthInfo = getPasswordStrengthLabel(passwordStrength);

  return (
    <div className="auth-page-shell">
      <div className="signup-page">
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
          --gold-light: #FFF5CC;
          --cyan: #00D4FF;
          --gray-50: #F8F9FA;
          --gray-100: #E9ECEF;
          --gray-200: #DEE2E6;
          --gray-300: #CED4DA;
          --gray-600: #6C757D;
          --gray-700: #495057;
          --gray-900: #0A0E14;
          --red: #FF3B30;
          --green: #00C853;
          --orange: #FF9500;
        }

        body {
          font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--white);
          color: var(--gray-900);
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        .signup-page {
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

        .auth-page-shell > .signup-page {
          flex: 1;
        }

        .signup-page::before {
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

        .signup-page::after {
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
          max-width: 520px;
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
          margin-bottom: 2rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-logo {
          display: flex;
          align-items: center;
          justify-content: flex-start;
        }

        .form-title {
          font-size: 2.25rem;
          font-weight: 700;
          color: var(--gray-900);
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

        .account-type-selector {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 2rem;
        }

        .account-type-card {
          padding: 1.5rem;
          border: 2px solid var(--gray-200);
          border-radius: 16px;
          cursor: pointer;
          transition: all 0.2s ease;
          text-align: center;
          background: white;
        }

        .account-type-card:hover {
          border-color: var(--blue);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 102, 255, 0.12);
        }

        .account-type-card.active {
          border-color: var(--blue);
          background: var(--blue-light);
        }

        .account-type-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 1rem;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--gray-100);
          color: var(--gray-600);
          transition: all 0.2s ease;
        }

        .account-type-card.active .account-type-icon {
          background: var(--blue);
          color: white;
        }

        .account-type-label {
          font-weight: 600;
          color: var(--gray-900);
          margin-bottom: 0.25rem;
        }

        .account-type-description {
          font-size: 0.85rem;
          color: var(--gray-600);
        }

        .signup-form {
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

        .password-strength {
          margin-top: 0.75rem;
        }

        .strength-bar {
          height: 4px;
          background: var(--gray-200);
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 0.5rem;
        }

        .strength-fill {
          height: 100%;
          transition: all 0.3s ease;
          border-radius: 4px;
        }

        .strength-label {
          display: flex;
          justify-content: space-between;
          font-size: 0.85rem;
          font-weight: 500;
        }

        .strength-text {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .strength-requirements {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          margin-top: 0.75rem;
          font-size: 0.85rem;
        }

        .requirement-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--gray-600);
        }

        .requirement-item.met {
          color: var(--green);
        }

        .requirement-check {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          border: 2px solid var(--gray-300);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .requirement-item.met .requirement-check {
          background: var(--green);
          border-color: var(--green);
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

        .signin-prompt {
          text-align: center;
          font-size: 0.95rem;
          color: var(--gray-600);
        }

        .signin-link {
          color: var(--blue);
          font-weight: 600;
          text-decoration: none;
          cursor: pointer;
          transition: color 0.2s ease;
        }

        .signin-link:hover {
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

          .account-type-selector {
            grid-template-columns: 1fr;
          }

          .signup-page::before,
          .signup-page::after {
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
            <h1 className="brand-title">Start Your Journey</h1>
            <p className="brand-subtitle">
              Join thousands of job seekers and recruiters transforming the hiring process with
              AI-powered intelligence.
            </p>

            <div className="brand-features">
              <div className="feature-item">
                <div className="feature-icon">
                  <Sparkles size={24} />
                </div>
                <div className="feature-text">AI-powered resume screening in seconds</div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">
                  <Target size={24} />
                </div>
                <div className="feature-text">Smart candidate matching & ranking</div>
              </div>
              <div className="feature-item">
                <div className="feature-icon">
                  <Shield size={24} />
                </div>
                <div className="feature-text">Bias-free, transparent hiring process</div>
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
              <h2 className="form-title">Create Account</h2>
              <p className="form-subtitle">Choose your account type and get started in minutes</p>
            </div>

            {error && (
              <div className="alert">
                <AlertCircle size={20} />
                <span>{error}</span>
              </div>
            )}

            <div className="account-type-selector">
              <div
                className={`account-type-card ${accountType === 'personal' ? 'active' : ''}`}
                onClick={() => setAccountType('personal')}
              >
                <div className="account-type-icon">
                  <UserCircle2 size={24} />
                </div>
                <div className="account-type-label">Job Seeker</div>
                <div className="account-type-description">Find opportunities</div>
              </div>

              <div
                className={`account-type-card ${accountType === 'company' ? 'active' : ''}`}
                onClick={() => setAccountType('company')}
              >
                <div className="account-type-icon">
                  <Building2 size={24} />
                </div>
                <div className="account-type-label">Recruiter</div>
                <div className="account-type-description">Hire top talent</div>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="signup-form" noValidate>
              <div className="form-group">
                <label className="form-label">
                  {accountType === 'personal' ? 'Full Name' : 'Company Name'}
                </label>
                <div className="input-wrapper">
                  <span className="input-icon">
                    {accountType === 'personal' ? <User size={20} /> : <Building2 size={20} />}
                  </span>
                  <input
                    type="text"
                    className={`form-input ${
                      touched[accountType === 'personal' ? 'name' : 'companyName'] &&
                      validationErrors[accountType === 'personal' ? 'name' : 'companyName']
                        ? 'error'
                        : ''
                    }`}
                    placeholder={accountType === 'personal' ? 'John Doe' : 'Your Company Inc.'}
                    value={accountType === 'personal' ? formData.name : formData.companyName}
                    onChange={handleChange(accountType === 'personal' ? 'name' : 'companyName')}
                    onBlur={handleBlur(accountType === 'personal' ? 'name' : 'companyName')}
                    autoComplete={accountType === 'personal' ? 'name' : 'organization'}
                  />
                </div>
                {touched[accountType === 'personal' ? 'name' : 'companyName'] &&
                  validationErrors[accountType === 'personal' ? 'name' : 'companyName'] && (
                    <div className="error-message">
                      <AlertCircle size={16} />
                      <span>
                        {validationErrors[accountType === 'personal' ? 'name' : 'companyName']}
                      </span>
                    </div>
                  )}
              </div>

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
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleChange('password')}
                    onBlur={handleBlur('password')}
                    autoComplete="new-password"
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

                {formData.password && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div
                        className="strength-fill"
                        style={{
                          width: `${passwordStrength}%`,
                          background: strengthInfo.color
                        }}
                      />
                    </div>
                    <div className="strength-label">
                      <div className="strength-text">
                        <span style={{ color: strengthInfo.color }}>{strengthInfo.label}</span>
                      </div>
                      <span>{passwordStrength}%</span>
                    </div>

                    <div className="strength-requirements">
                      <div
                        className={`requirement-item ${formData.password.length >= 8 ? 'met' : ''}`}
                      >
                        <div className="requirement-check">
                          {formData.password.length >= 8 && <CheckCircle2 size={12} />}
                        </div>
                        <span>At least 8 characters</span>
                      </div>
                      <div
                        className={`requirement-item ${
                          /(?=.*[a-z])(?=.*[A-Z])/.test(formData.password) ? 'met' : ''
                        }`}
                      >
                        <div className="requirement-check">
                          {/(?=.*[a-z])(?=.*[A-Z])/.test(formData.password) && (
                            <CheckCircle2 size={12} />
                          )}
                        </div>
                        <span>Upper & lowercase letters</span>
                      </div>
                      <div
                        className={`requirement-item ${/(?=.*\d)/.test(formData.password) ? 'met' : ''}`}
                      >
                        <div className="requirement-check">
                          {/(?=.*\d)/.test(formData.password) && <CheckCircle2 size={12} />}
                        </div>
                        <span>At least one number</span>
                      </div>
                      <div
                        className={`requirement-item ${
                          /(?=.*[^a-zA-Z0-9])/.test(formData.password) ? 'met' : ''
                        }`}
                      >
                        <div className="requirement-check">
                          {/(?=.*[^a-zA-Z0-9])/.test(formData.password) && (
                            <CheckCircle2 size={12} />
                          )}
                        </div>
                        <span>At least one special character</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <button type="submit" className="submit-button" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 size={20} className="button-loader" />
                    <span>Creating account...</span>
                  </>
                ) : (
                  <>
                    <span>Create Account</span>
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

            <div className="signin-prompt">
              Already have an account?{' '}
              <span className="signin-link" onClick={onSwitchToLogin}>
                Sign in here
              </span>
            </div>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
