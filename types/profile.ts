export interface Skill {
  skill: string;
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}

export interface Experience {
  role: string;
  company: string;
  start_date: string;
  end_date?: string;
  current: boolean;
  description: string;
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  start_year: number;
  end_year?: number;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string;
  url?: string;
}

export interface PortfolioLink {
  type: 'github' | 'linkedin' | 'portfolio' | 'twitter' | 'other';
  url: string;
}

export interface JobPreferences {
  preferred_job_types: string[];
  remote_preference: 'remote' | 'hybrid' | 'onsite' | 'no_preference';
  salary_expectation_min?: number;
  salary_expectation_max?: number;
  salary_currency: string;
  availability: 'immediate' | '2_weeks' | '1_month' | 'not_looking';
}

export interface CompanyData {
  industry?: string;
  company_size?: string;
  website?: string;
  mission?: string;
  culture?: string;
  benefits?: string[];
  founded_year?: number;
  locations?: {
    address: string;
    city: string;
    state: string;
    country: string;
    is_hq: boolean;
  }[];
}

export interface ExtendedProfile {
  id: string;
  full_name: string | null;
  role: 'candidate' | 'recruiter';
  avatar_url: string | null;
  cover_url: string | null;
  bio: string | null;
  headline: string | null;
  location: string | null;
  phone: string | null;
  skills: Skill[];
  experience: Experience[];
  education: Education[];
  certifications: Certification[];
  portfolio_links: PortfolioLink[];
  job_preferences: JobPreferences;
  company_data: CompanyData;
  onboarding_completed: boolean;
  updated_at: string;
}
