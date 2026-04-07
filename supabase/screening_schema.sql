-- 1. Screening Sessions Table
CREATE TABLE IF NOT EXISTS public.screening_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'processing', 'completed', 'failed')) DEFAULT 'pending',
    total_files INT DEFAULT 0,
    processed_count INT DEFAULT 0,
    criteria JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Screening Results Table
CREATE TABLE IF NOT EXISTS public.screening_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES public.screening_sessions(id) ON DELETE CASCADE NOT NULL,
    candidate_name TEXT,
    candidate_email TEXT,
    resume_url TEXT NOT NULL,
    match_score INT DEFAULT 0,
    analysis JSONB NOT NULL DEFAULT '{}'::jsonb, -- {skills_score, exp_score, edu_score, keyword_matches, gaps, summary}
    status TEXT CHECK (status IN ('completed', 'failed')) DEFAULT 'completed',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Enable RLS
ALTER TABLE public.screening_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screening_results ENABLE ROW LEVEL SECURITY;

-- 4. RLS Policies for Sessions
CREATE POLICY "Companies can view their own screening sessions." ON public.screening_sessions
    FOR SELECT USING (auth.uid() = company_id);

CREATE POLICY "Companies can manage their own screening sessions." ON public.screening_sessions
    FOR ALL USING (auth.uid() = company_id);

-- 5. RLS Policies for Results (Cascade from sessions)
CREATE POLICY "Companies can view results for their sessions." ON public.screening_results
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM public.screening_sessions 
        WHERE id = session_id AND company_id = auth.uid()
    ));

-- 6. Storage Bucket: 'screening-resumes'
-- (Manual Action: Create bucket 'screening-resumes' in Supabase dashboard)
-- Policies for the bucket
CREATE POLICY "Recruiters can upload screening resumes" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'screening-resumes' AND 
    auth.role() = 'authenticated'
  );

CREATE POLICY "Recruiters can view screening resumes" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'screening-resumes' AND 
    auth.role() = 'authenticated'
  );

-- 7. RPC: Increment Processed Count
CREATE OR REPLACE FUNCTION public.increment_processed_count(session_row_id UUID)
RETURNS VOID AS $$
BEGIN
  UPDATE public.screening_sessions
  SET processed_count = processed_count + 1,
      status = CASE 
        WHEN (SELECT processed_count + 1 FROM public.screening_sessions WHERE id = session_row_id) >= (SELECT total_files FROM public.screening_sessions WHERE id = session_row_id) THEN 'completed' 
        ELSE 'processing' 
      END,
      updated_at = timezone('utc'::text, now())
  WHERE id = session_row_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
