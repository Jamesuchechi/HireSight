import type {
  DashboardStats,
  DashboardActivityListResponse,
  SavedJobListResponse,
  RecommendedJobListResponse,
  InterviewListResponse,
  CandidateListResponse,
  ApplicationListResponse
} from '../types';
import { apiClient } from './apiClient';

export const getDashboardStats = () =>
  apiClient.get<DashboardStats>('/dashboard/stats');

export const getDashboardActivities = () =>
  apiClient.get<DashboardActivityListResponse>('/dashboard/activities');

export const listSavedJobs = (params?: Record<string, unknown>) =>
  apiClient.get<SavedJobListResponse>('/jobs/saved', { params });

export const listRecommendedJobs = (params?: Record<string, unknown>) =>
  apiClient.get<RecommendedJobListResponse>('/jobs/recommended', { params });

export const listInterviews = (params?: Record<string, unknown>) =>
  apiClient.get<InterviewListResponse>('/interviews', { params });

export const listCandidates = (params?: Record<string, unknown>) =>
  apiClient.get<CandidateListResponse>('/candidates', { params });

export const listApplications = (params?: Record<string, unknown>) =>
  apiClient.get<ApplicationListResponse>('/applications', { params });
