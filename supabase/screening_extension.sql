-- 1. Extend screening_sessions with additional neural weights and question-specific criteria
ALTER TABLE public.screening_sessions 
ADD COLUMN IF NOT EXISTS weight_screening_questions INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS weight_assessments INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS screening_questions_config JSONB DEFAULT '{}'::jsonb;

-- 2. Add shortlist and dismissal tracking to screening_results
ALTER TABLE public.screening_results 
ADD COLUMN IF NOT EXISTS is_shortlisted BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_dismissed BOOLEAN DEFAULT false;
