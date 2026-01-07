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
  title: string;
  company?: string;
  description: string;
  requirements?: string;
  required_skills?: string[];
  required_experience_years?: number;
  required_education?: string;
  embedding_model?: string;
  created_date: string;
  updated_date?: string;
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
