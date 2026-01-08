import type { JobCreatePayload, JobOut, JobSearchResponse } from '../types';
import { apiClient } from './apiClient';

export const createJob = (payload: JobCreatePayload) =>
  apiClient.post<JobOut>('/jobs/', payload);

export const listJobs = () => apiClient.get<JobOut[]>('/jobs/');

export const closeJob = (jobId: string) =>
  apiClient.post<{ message: string; job: JobOut }>(`/jobs/${jobId}/close`);

export const duplicateJob = (jobId: string) =>
  apiClient.post<JobOut>(`/jobs/${jobId}/duplicate`);

export const getSimilarJobs = (jobId: string, limit: number = 3) =>
  apiClient.get<JobOut[]>(`/jobs/${jobId}/similar`, {
    params: { limit }
  });

export const searchJobs = (params: Record<string, unknown>) =>
  apiClient.get<JobSearchResponse>('/jobs/search', { params });
