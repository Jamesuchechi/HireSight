import { useState } from 'react';
import { Check, Mail, AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';

type Props = {
  email?: string | null;
  onVerify: (token: string) => Promise<void> | void;
  onBackToLogin: () => void;
  onResendVerification?: () => Promise<void> | void;
  statusMessage?: string | null;
  error?: string | null;
  isLoading?: boolean;
};

export default function EmailVerificationPage({
  email,
  onVerify,
  onBackToLogin,
  onResendVerification,
  statusMessage,
  error,
  isLoading = false
}: Props) {
  const [token, setToken] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLocalError(null);

    if (!token.trim()) {
      setLocalError('Please enter the verification token');
      return;
    }

    // Basic token format validation (assuming UUID format)
    if (token.trim().length < 8) {
      setLocalError('Token appears to be incomplete');
      return;
    }

    await onVerify(token.trim());
  };

  const handleResend = async () => {
    if (!onResendVerification || resendCooldown > 0) return;

    setIsResending(true);
    setLocalError(null);
    setResendSuccess(false);

    try {
      await onResendVerification();
      setResendSuccess(true);

      // Start 60-second cooldown
      setResendCooldown(60);
      const interval = setInterval(() => {
        setResendCooldown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      // Hide success message after 5 seconds
      setTimeout(() => setResendSuccess(false), 5000);
    } catch (err) {
      setLocalError('Failed to resend verification email. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  const displayError = error || localError;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-cyan-50 flex items-center justify-center p-4">
      {/* Decorative Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-float"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-100 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-float-delayed"></div>
      </div>

      <div className="relative w-full max-w-md">
        {/* Back to Login Button */}
        <button
          onClick={onBackToLogin}
          className="mb-6 flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors group"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm font-medium">Back to Sign In</span>
        </button>

        {/* Main Card */}
        <div className="bg-white rounded-3xl shadow-2xl shadow-blue-500/10 p-8 md:p-10 border border-gray-100">
          {/* Icon */}
          <div className="mb-6 flex justify-center">
            <div className="relative">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Mail className="w-10 h-10 text-white" />
              </div>
              {statusMessage && statusMessage.toLowerCase().includes('verified') && (
                <div className="absolute -top-1 -right-1 w-7 h-7 bg-green-500 rounded-full flex items-center justify-center shadow-lg animate-scale-in">
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}
            </div>
          </div>

          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-3" style={{ fontFamily: 'Clash Display, sans-serif' }}>
              Verify Your Email
            </h1>
            <p className="text-gray-600 leading-relaxed">
              We sent a verification token to{' '}
              <span className="font-semibold text-gray-900">{email ?? 'your inbox'}</span>
              . Enter it below to activate your account.
            </p>
          </div>

          {/* Status Messages */}
          {statusMessage && (
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-3 animate-fade-in-up">
              <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Check className="w-3 h-3 text-white" />
              </div>
              <p className="text-sm text-blue-900 flex-1">{statusMessage}</p>
            </div>
          )}

          {displayError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3 animate-shake">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-900 flex-1">{displayError}</p>
            </div>
          )}

          {resendSuccess && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl flex items-start gap-3 animate-fade-in-up">
              <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-900 flex-1">Verification email sent! Check your inbox.</p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="token" className="block text-sm font-medium text-gray-700 mb-2">
                Verification Token
              </label>
              <input
                id="token"
                type="text"
                placeholder="Enter your verification token"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                disabled={isLoading}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all disabled:bg-gray-50 disabled:cursor-not-allowed text-center text-lg tracking-wider font-mono"
                required
                autoComplete="off"
                spellCheck="false"
              />
              <p className="mt-2 text-xs text-gray-500 text-center">
                The token is case-sensitive and expires in 24 hours
              </p>
            </div>

            <button
              type="submit"
              disabled={isLoading || !token.trim()}
              className="w-full py-3.5 bg-gradient-to-r from-blue-600 to-blue-500 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:-translate-y-0.5 disabled:hover:translate-y-0 disabled:hover:shadow-lg flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <>
                  <Check className="w-5 h-5" />
                  <span>Verify & Continue</span>
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="my-8 flex items-center gap-4">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
            <span className="text-xs text-gray-500 font-medium">OR</span>
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent"></div>
          </div>

          {/* Resend Section */}
          <div className="text-center space-y-4">
            <p className="text-sm text-gray-600">
              Didn't receive the email?
            </p>

            {onResendVerification && (
              <button
                onClick={handleResend}
                disabled={isResending || resendCooldown > 0}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`w-4 h-4 ${isResending ? 'animate-spin' : ''}`} />
                <span>
                  {isResending
                    ? 'Sending...'
                    : resendCooldown > 0
                      ? `Resend in ${resendCooldown}s`
                      : 'Resend Verification Email'}
                </span>
              </button>
            )}

            <div className="pt-4 space-y-2 text-xs text-gray-500">
              <p>• Check your spam or junk folder</p>
              <p>• Make sure the email address is correct</p>
              <p>• Contact support if you still need help</p>
            </div>
          </div>

          {/* Footer Note */}
          <div className="mt-8 pt-6 border-t border-gray-200">
            <p className="text-center text-sm text-gray-600">
              Already verified?{' '}
              <button
                onClick={onBackToLogin}
                className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
              >
                Sign in to your account
              </button>
            </p>
          </div>
        </div>

        {/* Help Text */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Need help?{' '}
            <a href="mailto:support@hiresight.io" className="text-blue-600 hover:text-blue-700 font-medium hover:underline">
              Contact Support
            </a>
          </p>
        </div>
      </div>

      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(5deg); }
        }

        @keyframes float-delayed {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-30px) rotate(-5deg); }
        }

        @keyframes fade-in-up {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        @keyframes scale-in {
          from {
            opacity: 0;
            transform: scale(0);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .animate-float {
          animation: float 25s ease-in-out infinite;
        }

        .animate-float-delayed {
          animation: float-delayed 30s ease-in-out infinite;
          animation-delay: 2s;
        }

        .animate-fade-in-up {
          animation: fade-in-up 0.4s ease-out;
        }

        .animate-shake {
          animation: shake 0.4s ease-out;
        }

        .animate-scale-in {
          animation: scale-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}