import { apiClient } from './apiClient';

export const uploadResume = (formData: FormData) =>
  apiClient.post('/upload-resume/', formData);
