-- SQL to update existing profiles table with additional fields for professional data
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS headline TEXT,
ADD COLUMN IF NOT EXISTS location TEXT,
ADD COLUMN IF NOT EXISTS phone TEXT,
ADD COLUMN IF NOT EXISTS skills JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS experience JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS education JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS certifications JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS portfolio_links JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS job_preferences JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS company_data JSONB DEFAULT '{}'::jsonb;
