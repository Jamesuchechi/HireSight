import React from 'react';
import { LogOut, ArrowLeft, Loader2, Shield, CheckCircle2 } from 'lucide-react';
import Logo from './Logo';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type LogoutPromptProps = {
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function LogoutPrompt({ onConfirm, onCancel, isLoading = false }: LogoutPromptProps) {
  return (
    <div className="logout-page">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
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
          --green: #00C853;
        }

        body {
          font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--white);
          color: var(--gray-900);
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        .logout-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          position: relative;
          overflow: hidden;
          background: linear-gradient(135deg, var(--gray-50) 0%, var(--white) 100%);
        }

        /* Animated Background Orbs */
        .logout-page::before {
          content: '';
          position: absolute;
          top: -20%;
          right: -15%;
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, var(--blue) 0%, transparent 70%);
          filter: blur(100px);
          opacity: 0.2;
          animation: float 20s infinite ease-in-out;
        }

        .logout-page::after {
          content: '';
          position: absolute;
          bottom: -20%;
          left: -15%;
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, var(--cyan) 0%, transparent 70%);
          filter: blur(100px);
          opacity: 0.18;
          animation: float 25s infinite ease-in-out reverse;
        }

        .logout-orb {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, var(--gold) 0%, transparent 70%);
          filter: blur(90px);
          opacity: 0.12;
          animation: float 18s infinite ease-in-out;
          animation-delay: -5s;
        }

        @keyframes float {
          0%, 100% { transform: translate(-50%, -50%) scale(1) rotate(0deg); }
          33% { transform: translate(calc(-50% + 40px), calc(-50% - 40px)) scale(1.1) rotate(120deg); }
          66% { transform: translate(calc(-50% - 30px), calc(-50% + 30px)) scale(0.9) rotate(240deg); }
        }

        .logout-container {
          width: 100%;
          max-width: 520px;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(20px);
          border-radius: 32px;
          padding: 3rem;
          box-shadow: 0 24px 80px rgba(0, 0, 0, 0.12);
          border: 1px solid rgba(255, 255, 255, 0.8);
          position: relative;
          z-index: 1;
          animation: scaleIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(20px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }

        .logout-header {
          text-align: center;
          margin-bottom: 2rem;
        }

        .logout-logo {
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 2rem;
          animation: fadeInDown 0.8s ease forwards;
        }

        @keyframes fadeInDown {
          from {
            opacity: 0;
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .logout-icon-wrapper {
          width: 80px;
          height: 80px;
          border-radius: 24px;
          background: linear-gradient(135deg, var(--blue) 0%, var(--cyan) 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 1.5rem;
          box-shadow: 0 8px 32px rgba(0, 102, 255, 0.3);
          animation: pulse 2s ease infinite;
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(1);
            box-shadow: 0 8px 32px rgba(0, 102, 255, 0.3);
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 12px 40px rgba(0, 102, 255, 0.4);
          }
        }

        .logout-icon-wrapper svg {
          color: white;
        }

        .logout-title {
          font-size: 2.25rem;
          font-weight: 700;
          color: var(--gray-900);
          margin-bottom: 0.75rem;
          letter-spacing: -0.02em;
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: 0.1s;
          opacity: 0;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .logout-subtitle {
          font-size: 1.1rem;
          color: var(--gray-600);
          line-height: 1.6;
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: 0.2s;
          opacity: 0;
        }

        .logout-features {
          margin: 2rem 0;
          padding: 1.5rem;
          background: var(--gray-50);
          border-radius: 16px;
          border: 1px solid var(--gray-200);
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: 0.3s;
          opacity: 0;
        }

        .feature-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .feature-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
          color: var(--gray-700);
        }

        .feature-icon {
          width: 24px;
          height: 24px;
          border-radius: 8px;
          background: var(--green);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .logout-actions {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          animation: fadeInUp 0.8s ease forwards;
          animation-delay: 0.4s;
          opacity: 0;
        }

        .logout-button {
          width: 100%;
          padding: 1.25rem;
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
          position: relative;
          overflow: hidden;
        }

        .logout-button::before {
          content: '';
          position: absolute;
          top: 50%;
          left: 50%;
          width: 0;
          height: 0;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.2);
          transform: translate(-50%, -50%);
          transition: width 0.6s, height 0.6s;
        }

        .logout-button:active::before {
          width: 300px;
          height: 300px;
        }

        .logout-button-primary {
          background: var(--blue);
          color: white;
        }

        .logout-button-primary:hover:not(:disabled) {
          background: var(--blue-dark);
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(0, 102, 255, 0.3);
        }

        .logout-button-primary:active:not(:disabled) {
          transform: translateY(0);
        }

        .logout-button-primary:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .logout-button-secondary {
          background: white;
          color: var(--gray-700);
          border: 2px solid var(--gray-200);
        }

        .logout-button-secondary:hover:not(:disabled) {
          background: var(--gray-50);
          border-color: var(--gray-300);
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        }

        .logout-button-secondary:active:not(:disabled) {
          transform: translateY(0);
        }

        .button-loader {
          animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .logout-footer {
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid var(--gray-200);
          text-align: center;
          animation: fadeIn 0.8s ease forwards;
          animation-delay: 0.5s;
          opacity: 0;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .logout-footer-text {
          font-size: 0.9rem;
          color: var(--gray-600);
          line-height: 1.6;
        }

        .logout-footer-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 20px;
          height: 20px;
          border-radius: 6px;
          background: var(--blue-light);
          color: var(--blue);
          margin: 0 0.25rem;
          vertical-align: middle;
        }

        /* Responsive Design */
        @media (max-width: 640px) {
          .logout-page {
            padding: 1rem;
          }

          .logout-container {
            padding: 2rem 1.5rem;
            border-radius: 24px;
          }

          .logout-title {
            font-size: 1.75rem;
          }

          .logout-subtitle {
            font-size: 1rem;
          }

          .logout-icon-wrapper {
            width: 64px;
            height: 64px;
          }

          .logout-page::before,
          .logout-page::after {
            width: 400px;
            height: 400px;
          }
        }

        /* Hover effects */
        @media (hover: hover) {
          .logout-button {
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          }
        }

        /* Accessibility */
        .logout-button:focus-visible {
          outline: 3px solid var(--blue);
          outline-offset: 3px;
        }

        /* Reduced motion */
        @media (prefers-reduced-motion: reduce) {
          * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
      `}</style>

      <div className="logout-orb" />

      <div className="logout-container">
        <div className="logout-header">
          <div className="logout-logo">
            <Logo showText={false} size="small" animated />
          </div>

          <div className="logout-icon-wrapper">
            <LogOut size={36} strokeWidth={2} />
          </div>

          <h1 className="logout-title">Leaving Already?</h1>
          <p className="logout-subtitle">
            We'll save your progress and keep everything secure. You can come back anytime to
            continue where you left off.
          </p>
        </div>

        <div className="logout-features">
          <div className="feature-list">
            <div className="feature-item">
              <div className="feature-icon">
                <CheckCircle2 size={14} strokeWidth={3} />
              </div>
              <span>All your data is automatically saved</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <CheckCircle2 size={14} strokeWidth={3} />
              </div>
              <span>Your applications and profile are secure</span>
            </div>
            <div className="feature-item">
              <div className="feature-icon">
                <CheckCircle2 size={14} strokeWidth={3} />
              </div>
              <span>Resume wherever you stopped</span>
            </div>
          </div>
        </div>

        <div className="logout-actions">
          <button
            className="logout-button logout-button-primary"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="button-loader" />
                <span>Logging out...</span>
              </>
            ) : (
              <>
                <LogOut size={20} />
                <span>Yes, Log Me Out</span>
              </>
            )}
          </button>

          <button
            className="logout-button logout-button-secondary"
            onClick={onCancel}
            disabled={isLoading}
          >
            <ArrowLeft size={20} />
            <span>Go Back</span>
          </button>
        </div>

        <div className="logout-footer">
          <p className="logout-footer-text">
            <span className="logout-footer-icon">
              <Shield size={12} />
            </span>
            Your session is protected with enterprise-grade security
          </p>
        </div>
      </div>
    </div>
  );
}