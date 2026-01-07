import { apiClient } from './apiClient';
import type { AuthResponse, SignInPayload, SignUpPayload } from '../types';

export const signIn = (payload: SignInPayload) =>
  apiClient.post<AuthResponse>('/auth/login', payload);

export const signUp = (payload: SignUpPayload) =>
  apiClient.post<AuthResponse>('/auth/register', payload);
