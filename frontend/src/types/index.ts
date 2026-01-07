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
