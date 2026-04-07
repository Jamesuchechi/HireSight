-- 1. Enable PostGIS for radius-based search
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Jobs Table
CREATE TABLE public.jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL, -- JSON or HTML content for rich text
    requirements TEXT,
    salary_min NUMERIC,
    salary_max NUMERIC,
    currency TEXT DEFAULT 'USD',
    location TEXT,
    location_coords GEOGRAPHY(POINT, 4326), -- For radius search
    remote_type TEXT CHECK (remote_type IN ('remote', 'hybrid', 'onsite')) NOT NULL,
    experience_level TEXT CHECK (experience_level IN ('entry', 'mid', 'senior', 'lead', 'executive')) NOT NULL,
    job_type TEXT CHECK (job_type IN ('full-time', 'part-time', 'contract', 'internship')) NOT NULL,
    status TEXT CHECK (status IN ('draft', 'active', 'closed', 'deleted')) DEFAULT 'draft',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Job Skills Table (Tagging)
CREATE TABLE public.job_skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    skill_name TEXT NOT NULL,
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Screening Questions
CREATE TABLE public.job_screening_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    question TEXT NOT NULL,
    input_type TEXT CHECK (input_type IN ('short_text', 'long_text', 'yes_no', 'multiple_choice')) NOT NULL,
    options JSONB, -- For multiple_choice types
    is_required BOOLEAN DEFAULT true,
    order_index INT DEFAULT 0
);

-- 5. Job Applications
CREATE TABLE public.job_applications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    candidate_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE SET NULL,
    answers JSONB, -- Key-value pair: question_id -> response
    status TEXT CHECK (status IN ('applied', 'screening', 'interview', 'offer', 'hired', 'rejected')) DEFAULT 'applied',
    match_score NUMERIC, -- AI calculated score
    source TEXT, -- Discovery source
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(job_id, candidate_id) -- Prevent duplicate applications
);

-- 6. Saved Jobs (Bookmarks)
CREATE TABLE public.saved_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(job_id, user_id)
);

-- 7. Job Views (Analytics)
CREATE TABLE public.job_views (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL, -- Allow tracking for logged-in users
    viewer_ip TEXT, -- For unique view calculation
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 8. Saved Searches
CREATE TABLE public.saved_searches (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    filters JSONB NOT NULL, -- Serialized filter state
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_screening_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.saved_searches ENABLE ROW LEVEL SECURITY;

-- POLICIES: JOBS
CREATE POLICY "Jobs are viewable by everyone if active." ON public.jobs
    FOR SELECT USING (status = 'active');

CREATE POLICY "Companies can manage their own jobs." ON public.jobs
    FOR ALL USING (auth.uid() = company_id);

-- POLICIES: SKILLS & QUESTIONS
CREATE POLICY "Skills are viewable by everyone." ON public.job_skills
    FOR SELECT USING (true);

CREATE POLICY "Companies can manage their own job skills." ON public.job_skills
    FOR ALL USING (EXISTS (SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()));

CREATE POLICY "Questions are viewable by candidates applying." ON public.job_screening_questions
    FOR SELECT USING (true); -- Usually restricted to applicants but simpler for lookup

CREATE POLICY "Companies can manage their own job questions." ON public.job_screening_questions
    FOR ALL USING (EXISTS (SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()));

-- POLICIES: APPLICATIONS
CREATE POLICY "Candidates can view their own applications." ON public.job_applications
    FOR SELECT USING (auth.uid() = candidate_id);

CREATE POLICY "Candidates can submit applications." ON public.job_applications
    FOR INSERT WITH CHECK (auth.uid() = candidate_id);

CREATE POLICY "Companies can view applications for their jobs." ON public.job_applications
    FOR SELECT USING (EXISTS (SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()));

CREATE POLICY "Companies can update application status." ON public.job_applications
    FOR UPDATE USING (EXISTS (SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()));

-- POLICIES: SAVED JOBS & SEARCHES
CREATE POLICY "Users can manage their own saved jobs." ON public.saved_jobs
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage their own saved searches." ON public.saved_searches
    FOR ALL USING (auth.uid() = user_id);

-- POLICIES: ANALYTICS (VIEWS)
CREATE POLICY "Anonymous users can insert views." ON public.job_views
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Companies can view analytics for their jobs." ON public.job_views
    FOR SELECT USING (EXISTS (SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()));

-- UPDATE TRIGGERS
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON public.jobs FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_job_applications_updated_at BEFORE UPDATE ON public.job_applications FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
