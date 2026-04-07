-- 1. Assessments Table (Test Definitions)
CREATE TABLE public.assessments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    creator_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    duration_minutes INT DEFAULT 30,
    passing_score INT DEFAULT 60,
    category TEXT DEFAULT 'technical',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Assessment Questions (Pool)
CREATE TABLE public.assessment_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    assessment_id UUID REFERENCES public.assessments(id) ON DELETE CASCADE NOT NULL,
    question_text TEXT NOT NULL,
    question_type TEXT CHECK (question_type IN ('mcq', 'checkbox', 'short_answer')) DEFAULT 'mcq',
    options JSONB, -- Array of strings for MCQ/Checkbox
    correct_answer TEXT NOT NULL, -- Key or string
    points INT DEFAULT 1,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Assessment Attempts (Results)
CREATE TABLE public.assessment_attempts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    assessment_id UUID REFERENCES public.assessments(id) ON DELETE CASCADE NOT NULL,
    candidate_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    job_application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE,
    answers JSONB, -- Map: question_id -> candidate_response
    score NUMERIC,
    total_points INT,
    status TEXT CHECK (status IN ('started', 'completed', 'timed_out')) DEFAULT 'started',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 4. Enable RLS
ALTER TABLE public.assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assessment_attempts ENABLE ROW LEVEL SECURITY;

-- 5. POLICIES: ASSESSMENTS
CREATE POLICY "Recruiters can manage their own assessments." ON public.assessments
    FOR ALL USING (auth.uid() = creator_id);

CREATE POLICY "Candidates can view assessments assigned to them." ON public.assessments
    FOR SELECT USING (
        is_active = true AND (
            job_id IS NULL OR 
            EXISTS (SELECT 1 FROM public.job_applications WHERE job_id = assessments.job_id AND candidate_id = auth.uid())
        )
    );

-- 6. POLICIES: QUESTIONS
CREATE POLICY "Recruiters can manage their questions." ON public.assessment_questions
    FOR ALL USING (EXISTS (SELECT 1 FROM public.assessments WHERE id = assessment_id AND creator_id = auth.uid()));

CREATE POLICY "Candidates can view questions during an active attempt." ON public.assessment_questions
    FOR SELECT USING (EXISTS (SELECT 1 FROM public.assessment_attempts WHERE assessment_id = assessment_questions.assessment_id AND candidate_id = auth.uid() AND status = 'started'));

-- 7. POLICIES: ATTEMPTS
CREATE POLICY "Candidates can manage their own attempts." ON public.assessment_attempts
    FOR ALL USING (auth.uid() = candidate_id);

CREATE POLICY "Recruiters can view attempts for their assessments." ON public.assessment_attempts
    FOR SELECT USING (EXISTS (SELECT 1 FROM public.assessments WHERE id = assessment_id AND creator_id = auth.uid()));

-- UPDATE TRIGGERS
CREATE TRIGGER update_assessments_updated_at BEFORE UPDATE ON public.assessments FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
