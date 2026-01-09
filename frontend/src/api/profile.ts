import { apiClient } from './apiClient';

interface ProfileUpdatePayload {
    full_name?: string;
    headline?: string;
    location?: string;
    phone?: string;
    bio?: string;
    skills?: Array<{ skill: string; proficiency?: string }>;
    experience?: Array<{
        company?: string;
        role?: string;
        start_date?: string;
        end_date?: string;
        description?: string;
    }>;
    education?: Array<{
        institution?: string;
        degree?: string;
        field?: string;
        start_date?: string;
        end_date?: string;
    }>;
}

export const updateProfile = (payload: ProfileUpdatePayload) =>
    apiClient.put('/users/me/profile', payload);
