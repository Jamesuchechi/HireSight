import { useEffect, useState } from 'react';
import axios from 'axios';
import HireSightLanding from './components/HireSightLanding';
import Dashboard from './components/Dashboard';
import type {
  AuthResponse,
  AuthUser,
  SignInPayload,
  SignUpPayload,
} from './types';
import { signIn, signUp } from './api/auth';
import { setAuthToken } from './api/apiClient';

const TOKEN_KEY = 'hiresight_access_token';
const USER_KEY = 'hiresight_user';

function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

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
    setAuthError(null);
  };

  const clearSession = () => {
    setAuthToken(undefined);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
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

  const handleSignIn = async (payload: SignInPayload) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const { data } = await signIn(payload);
      persistSession(data);
    } catch (error) {
      setAuthError(buildErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (payload: SignUpPayload) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const { data } = await signUp(payload);
      persistSession(data);
    } catch (error) {
      setAuthError(buildErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignOut = () => {
    clearSession();
  };

  if (!user) {
    return (
      <HireSightLanding
        onSignIn={handleSignIn}
        onSignUp={handleSignUp}
        authError={authError}
        isLoading={isLoading}
      />
    );
  }

  return <Dashboard user={user} onSignOut={handleSignOut} />;
}

export default App;
