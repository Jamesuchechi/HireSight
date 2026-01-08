import type { ResumeListResponse, ResumeOut } from '../types';
import { apiClient } from './apiClient';

export const uploadResume = (formData: FormData) =>
  apiClient.post<ResumeOut>('/resumes/upload', formData);

export const listResumes = () =>
  apiClient.get<ResumeListResponse>('/resumes');

export const parseResume = (resumeId: string) =>
  apiClient.post<ResumeOut>(`/resumes/${resumeId}/parse`);
