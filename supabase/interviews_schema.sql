-- ============================================================
-- EXTENSIONS
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- INTERVIEWS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS application_id UUID;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS type TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'scheduled';
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMPTZ;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS duration_minutes INT DEFAULT 60;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS timezone TEXT DEFAULT 'UTC';
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS location TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS video_url TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS candidate_response TEXT DEFAULT 'pending';
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS proposed_times JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS company_notes TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS candidate_instructions TEXT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- ============================================================
-- SAFE LEGACY CLEANUP (IF CONFLICTS EXIST)
-- ============================================================
DO $$ BEGIN
    ALTER TABLE public.interviews ALTER COLUMN job_id DROP NOT NULL;
EXCEPTION WHEN undefined_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE public.interviews ALTER COLUMN candidate_id DROP NOT NULL;
EXCEPTION WHEN undefined_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE public.interviews ALTER COLUMN start_time DROP NOT NULL;
EXCEPTION WHEN undefined_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE public.interviews ALTER COLUMN end_time DROP NOT NULL;
EXCEPTION WHEN undefined_column THEN NULL; END $$;

-- ============================================================
-- SAFE CONSTRAINTS
-- ============================================================

DO $$ BEGIN
    ALTER TABLE public.interviews DROP CONSTRAINT IF EXISTS interviews_type_check;
    ALTER TABLE public.interviews ADD CONSTRAINT interviews_type_check
    CHECK (type IN ('phone','video','onsite','technical','behavioral','panel'));
END $$;

DO $$ BEGIN
    ALTER TABLE public.interviews DROP CONSTRAINT IF EXISTS interviews_status_check;
    ALTER TABLE public.interviews ADD CONSTRAINT interviews_status_check
    CHECK (status IN ('scheduled','rescheduled','completed','cancelled','no_show'));
END $$;

DO $$ BEGIN
    ALTER TABLE public.interviews DROP CONSTRAINT IF EXISTS interviews_candidate_response_check;
    ALTER TABLE public.interviews ADD CONSTRAINT interviews_candidate_response_check
    CHECK (candidate_response IN ('pending','accepted','declined','proposed_reschedule'));
END $$;

-- ============================================================
-- SAFE FOREIGN KEYS (HARDENED RELATIONSHIPS)
-- ============================================================
DO $$ BEGIN
    -- Re-assert application_id relationship
    ALTER TABLE public.interviews DROP CONSTRAINT IF EXISTS interviews_application_id_fkey;
    ALTER TABLE public.interviews
    ADD CONSTRAINT interviews_application_id_fkey
    FOREIGN KEY (application_id)
    REFERENCES public.job_applications(id)
    ON DELETE CASCADE;
END $$;

DO $$ BEGIN
    -- Ensure interview_id relationship
    ALTER TABLE public.interview_participants DROP CONSTRAINT IF EXISTS interview_participants_interview_id_fkey;
    ALTER TABLE public.interview_participants
    ADD CONSTRAINT interview_participants_interview_id_fkey
    FOREIGN KEY (interview_id)
    REFERENCES public.interviews(id)
    ON DELETE CASCADE;
END $$;

-- ============================================================
-- INTERVIEW PARTICIPANTS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_participants ADD COLUMN IF NOT EXISTS interview_id UUID;
ALTER TABLE public.interview_participants ADD COLUMN IF NOT EXISTS profile_id UUID;
ALTER TABLE public.interview_participants ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'interviewer';
ALTER TABLE public.interview_participants ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT false;
ALTER TABLE public.interview_participants ADD COLUMN IF NOT EXISTS joined_at TIMESTAMPTZ;

-- ✅ SAFE UNIQUE
CREATE UNIQUE INDEX IF NOT EXISTS interview_participants_unique
ON public.interview_participants (interview_id, profile_id);

-- ============================================================
-- VIDEO SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_video_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS interview_id UUID;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS room_name TEXT;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS recording_url TEXT;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS transcript TEXT;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS ai_summary JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ;
ALTER TABLE public.interview_video_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

-- ✅ SAFE UNIQUE
CREATE UNIQUE INDEX IF NOT EXISTS interview_video_sessions_unique
ON public.interview_video_sessions (interview_id);

-- ============================================================
-- CODING SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_coding_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS interview_id UUID;
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'javascript';
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS problem_statement TEXT;
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS starter_code TEXT;
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS final_code TEXT;
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS execution_results JSONB DEFAULT '[]'::jsonb;
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE public.interview_coding_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- ============================================================
-- FEEDBACK
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS interview_id UUID;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS interviewer_id UUID;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS template_id UUID;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS overall_score NUMERIC;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS scores_json JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS recommendation TEXT;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE public.interview_feedback ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();

-- ✅ SAFE UNIQUE
CREATE UNIQUE INDEX IF NOT EXISTS interview_feedback_unique
ON public.interview_feedback (interview_id, interviewer_id);

-- ============================================================
-- PRACTICE SESSIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_practice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS candidate_id UUID;
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS job_id UUID;
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS difficulty TEXT;
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS focus_areas TEXT[];
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS type TEXT DEFAULT 'standard';
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS overall_score NUMERIC;
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS ai_report JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE public.interview_practice_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- ============================================================
-- PRACTICE QUESTIONS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.practice_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS session_id UUID;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS prompt TEXT;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS answer_transcript TEXT;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS audio_url TEXT;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS video_url TEXT;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS ai_feedback JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS score NUMERIC;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS order_index INT DEFAULT 0;
ALTER TABLE public.practice_questions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

-- ============================================================
-- ACTIVITY LOGS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.interview_activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS interview_id UUID;
ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS actor_id UUID;
ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.interview_activity_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

-- ============================================================
-- TRIGGER FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION log_interview_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO public.interview_activity_logs (interview_id, actor_id, action, notes)
        VALUES (NEW.id, auth.uid(), 'status_change',
        'Status changed from ' || OLD.status || ' to ' || NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SAFE TRIGGER
-- ============================================================
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'on_interview_status_change'
    ) THEN
        CREATE TRIGGER on_interview_status_change
        AFTER UPDATE ON public.interviews
        FOR EACH ROW EXECUTE FUNCTION log_interview_activity();
    END IF;
END $$;

-- ============================================================
-- RLS
-- ============================================================
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_video_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_coding_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_practice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.practice_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_activity_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- POLICIES (SAFE & IDEMPOTENT)
-- ============================================================

-- Interviews
DROP POLICY IF EXISTS "Participants and hiring teams can view interviews." ON public.interviews;
CREATE POLICY "Participants and hiring teams can view interviews." ON public.interviews
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.job_applications ja
        LEFT JOIN public.jobs j ON ja.job_id = j.id
        WHERE ja.id = public.interviews.application_id 
        AND (ja.candidate_id = auth.uid() OR j.company_id = auth.uid())
    )
);

DROP POLICY IF EXISTS "Recruiters can manage interviews for their jobs." ON public.interviews;
CREATE POLICY "Recruiters can manage interviews for their jobs." ON public.interviews
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.job_applications ja
        JOIN public.jobs j ON ja.job_id = j.id
        WHERE ja.id = public.interviews.application_id AND j.company_id = auth.uid()
    )
);

-- Participants
DROP POLICY IF EXISTS "Participants in same interview can view each other." ON public.interview_participants;
CREATE POLICY "Participants in same interview can view each other." ON public.interview_participants
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM public.interviews i
        WHERE i.id = public.interview_participants.interview_id
    )
);

DROP POLICY IF EXISTS "Recruiters can manage interview participants." ON public.interview_participants;
CREATE POLICY "Recruiters can manage interview participants." ON public.interview_participants
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.interviews i
        WHERE i.id = public.interview_participants.interview_id
    )
);

-- Feedback
DROP POLICY IF EXISTS "Recruiters can manage feedback." ON public.interview_feedback;
CREATE POLICY "Recruiters can manage feedback." ON public.interview_feedback
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.interviews i
        JOIN public.job_applications ja ON i.application_id = ja.id
        JOIN public.jobs j ON ja.job_id = j.id
        WHERE i.id = public.interview_feedback.interview_id 
        AND j.company_id = auth.uid()
    )
);

-- Practice Sessions
DROP POLICY IF EXISTS "Candidates manage their own practice sessions." ON public.interview_practice_sessions;
CREATE POLICY "Candidates manage their own practice sessions." 
ON public.interview_practice_sessions
FOR ALL USING (auth.uid() = candidate_id);

DROP POLICY IF EXISTS "Candidates manage their own practice questions." ON public.practice_questions;
CREATE POLICY "Candidates manage their own practice questions." 
ON public.practice_questions
FOR ALL USING (
    EXISTS (
        SELECT 1 FROM public.interview_practice_sessions 
        WHERE id = session_id AND candidate_id = auth.uid()
    )
);