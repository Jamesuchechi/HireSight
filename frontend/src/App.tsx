import { useEffect, useState } from 'react';
import axios from 'axios';
import HireSightLanding from './components/HireSightLanding';
import Dashboard from './components/Dashboard';
import DashboardShell from './components/DashboardShell';
import LoginPage from './components/LoginPage';
import SignUpPage from './components/SignUpPage';
import EmailVerificationPage from './components/EmailVerificationPage';
import ForgotPasswordPage from './components/ForgotPasswordPage';
import ResetPasswordPage from './components/ResetPasswordPage';
import LogoutPrompt from './components/LogoutPrompt';
import type {
  AuthResponse,
  AuthUser,
  SignInPayload,
  SignUpPayload
} from './types';
import {
  signIn,
  signUp,
  verifyEmail,
  forgotPassword,
  resetPassword,
  logout as logoutRequest,
} from './api/auth';
import { setAuthToken } from './api/apiClient';

const TOKEN_KEY = 'hiresight_access_token';
const USER_KEY = 'hiresight_user';

type ViewState = 'landing' | 'login' | 'signup' | 'verify' | 'forgot' | 'reset' | 'logout';

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [view, setView] = useState<ViewState>('landing');
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [loginError, setLoginError] = useState<string | null>(null);
  const [signupError, setSignupError] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [resetError, setResetError] = useState<string | null>(null);
  const [loginLoading, setLoginLoading] = useState(false);
  const [signupLoading, setSignupLoading] = useState(false);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const storedUser = localStorage.getItem(USER_KEY);
    if (token && storedUser) {
      try {
        const parsedUser: AuthUser = JSON.parse(storedUser);
        setAuthToken(token);
        setUser(parsedUser);
      } catch {
        localStorage.removeItem(USER_KEY);
      }
    }
  }, []);

  const persistSession = (response: AuthResponse) => {
    setAuthToken(response.access_token);
    localStorage.setItem(TOKEN_KEY, response.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    setUser(response.user);
    setStatusMessage(null);
    setPendingEmail(null);
  };

  const clearSession = () => {
    setAuthToken(undefined);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setView('landing');
    setStatusMessage(null);
  };

  const buildErrorMessage = (error: unknown) => {
    if (axios.isAxiosError(error)) {
      return (
        (error.response?.data as { detail?: string })?.detail ??
        error.message
      );
    }
    if (error instanceof Error) {
      return error.message;
    }
    return 'Something went wrong. Please try again.';
  };

  const openLogin = () => {
    setLoginError(null);
    setStatusMessage(null);
    setView('login');
  };

  const openSignup = () => {
    setSignupError(null);
    setStatusMessage(null);
    setView('signup');
  };

  const openForgot = () => {
    setForgotError(null);
    setStatusMessage(null);
    setView('forgot');
  };

  const openReset = () => {
    setResetError(null);
    setStatusMessage(null);
    setView('reset');
  };

  const handleSignIn = async (payload: SignInPayload) => {
    setLoginLoading(true);
    setLoginError(null);
    try {
      const { data } = await signIn(payload);
      persistSession(data);
      setView('landing');
    } catch (error) {
      setLoginError(buildErrorMessage(error));
    } finally {
      setLoginLoading(false);
    }
  };

  const handleSignUp = async (payload: SignUpPayload) => {
    setSignupLoading(true);
    setSignupError(null);
    try {
      const { data } = await signUp(payload);
      setPendingEmail(payload.email);
      setStatusMessage(data.message);
      setView('verify');
    } catch (error) {
      setSignupError(buildErrorMessage(error));
    } finally {
      setSignupLoading(false);
    }
  };

  const handleVerify = async (token: string) => {
    setVerifyLoading(true);
    setVerifyError(null);
    try {
      const { data } = await verifyEmail({ token });
      persistSession(data);
      setView('landing');
    } catch (error) {
      setVerifyError(buildErrorMessage(error));
    } finally {
      setVerifyLoading(false);
    }
  };

  const handleForgot = async (email: string) => {
    setForgotLoading(true);
    setForgotError(null);
    try {
      const { data } = await forgotPassword({ email });
      setStatusMessage(data.message);
    } catch (error) {
      setForgotError(buildErrorMessage(error));
    } finally {
      setForgotLoading(false);
    }
  };

  const handleReset = async (token: string, newPassword: string) => {
    setResetLoading(true);
    setResetError(null);
    try {
      const { data } = await resetPassword({ token, new_password: newPassword });
      setStatusMessage(data.message);
      setView('login');
    } catch (error) {
      setResetError(buildErrorMessage(error));
    } finally {
      setResetLoading(false);
    }
  };

  const initiateLogout = () => {
    setView('logout');
  };

  const confirmLogout = async () => {
    try {
      await logoutRequest();
    } finally {
      clearSession();
    }
  };

  if (!user) {
    switch (view) {
      case 'login':
        return (
          <LoginPage
            isLoading={loginLoading}
            error={loginError}
            onSubmit={handleSignIn}
            onSwitchToSignup={openSignup}
            onForgotPassword={openForgot}
            statusMessage={statusMessage}
          />
        );
      case 'signup':
        return (
          <SignUpPage
            isLoading={signupLoading}
            error={signupError}
            onSubmit={handleSignUp}
            onSwitchToLogin={openLogin}
          />
        );
      case 'verify':
        return (
          <EmailVerificationPage
            email={pendingEmail}
            onVerify={handleVerify}
            onBackToLogin={openLogin}
            statusMessage={statusMessage}
            error={verifyError}
          />
        );
      case 'forgot':
        return (
          <ForgotPasswordPage
            isLoading={forgotLoading}
            onRequest={handleForgot}
            onBackToLogin={openLogin}
            statusMessage={statusMessage}
            error={forgotError}
          />
        );
      case 'reset':
        return (
          <ResetPasswordPage
            isLoading={resetLoading}
            onReset={handleReset}
            onBackToLogin={openLogin}
            statusMessage={statusMessage}
            error={resetError}
          />
        );
      default:
        return <HireSightLanding onShowLogin={openLogin} onShowSignup={openSignup} />;
    }
  }

  if (view === 'logout') {
    return <LogoutPrompt onConfirm={confirmLogout} onCancel={() => setView('landing')} />;
  }

  return <DashboardShell user={user} onSignOut={initiateLogout} />;
}

export default App;
