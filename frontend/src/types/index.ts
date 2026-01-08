export type JobCreatePayload = {
  title: string;
  company?: string;
  description: string;
  requirements?: string;
  required_skills?: string[];
  required_experience_years?: number;
  required_education?: string;
};

export type JobOut = {
  id: string;
  company_id: string;
  title: string;
  company?: string;
  description: string;
  requirements?: Record<string, unknown>;
  location?: string;
  remote_type?: string;
  employment_type?: string;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  screening_questions?: Record<string, unknown>[];
  status?: string;
  view_count?: number;
  application_count?: number;
  created_at: string;
  updated_at?: string;
  expires_at?: string;
  embedding_model?: string;
};

export type CandidatePreview = {
  id: string;
  name: string;
  score: number;
  match: string;
  skills: string[];
  status: string;
};

export type AccountType = 'personal' | 'company';

export type AuthUser = {
  id: string;
  email: string;
  account_type: AccountType;
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  full_name?: string;
  company_name?: string;
  role?: string;
};

export type SignInPayload = {
  email: string;
  password: string;
};

export type SignUpPayload = SignInPayload & {
  name: string;
  company_name?: string;
  account_type: AccountType;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: AuthUser;
};

export type VerifyPayload = {
  token: string;
};

export type ForgotPasswordPayload = {
  email: string;
};

export type ResetPasswordPayload = {
  token: string;
  new_password: string;
};

export type MessageResponse = {
  message: string;
};

export type ResumeOut = {
  id: string;
  user_id: string;
  filename: string;
  file_url: string;
  file_size?: number;
  version_name: string;
  is_primary: boolean;
  parsed_data: Record<string, unknown>;
  raw_text?: string;
  uploaded_at: string;
};

export type ResumeListResponse = {
  resumes: ResumeOut[];
  total: number;
};

export type JobSearchResponse = {
  jobs: JobOut[];
  total: number;
  page: number;
  limit: number;
};
