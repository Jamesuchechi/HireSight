import type { JobCreatePayload, JobOut } from '../types';
import { apiClient } from './apiClient';

export const createJob = (payload: JobCreatePayload) =>
  apiClient.post<JobOut>('/jobs/', payload);
