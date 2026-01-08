import { apiClient } from './apiClient';
import type {
  AuthResponse,
  SignInPayload,
  SignUpPayload,
  VerifyPayload,
  ForgotPasswordPayload,
  ResetPasswordPayload,
  MessageResponse
} from '../types';

export const signIn = (payload: SignInPayload) =>
  apiClient.post<AuthResponse>('/auth/login', payload);

export const signUp = (payload: SignUpPayload) =>
  apiClient.post<MessageResponse>('/auth/register', payload);

export const verifyEmail = (payload: VerifyPayload) =>
  apiClient.post<AuthResponse>('/auth/verify-email', payload);

export const forgotPassword = (payload: ForgotPasswordPayload) =>
  apiClient.post<MessageResponse>('/auth/forgot-password', payload);

export const resetPassword = (payload: ResetPasswordPayload) =>
  apiClient.post<MessageResponse>('/auth/reset-password', payload);

export const logout = () => apiClient.post<MessageResponse>('/auth/logout');
