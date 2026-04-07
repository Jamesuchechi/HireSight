-- ============================================================
-- HireSight: Interview Management System Schema
-- ============================================================

-- 1. Types & Enums (Using TEXT with CHECK constraints for flexibility)
-- interview_type: 'phone', 'video', 'onsite', 'technical', 'behavioral'
-- interview_status: 'scheduled', 'rescheduled', 'completed', 'cancelled', 'no_show'
-- participant_role: 'interviewer', 'candidate', 'observer'
-- candidate_response: 'pending', 'accepted', 'declined', 'proposed_reschedule'

-- 2. Interviews Table
CREATE TABLE public.interviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('phone', 'video', 'onsite', 'technical', 'behavioral', 'panel')),
    status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'rescheduled', 'completed', 'cancelled', 'no_show')),
    
    scheduled_at TIMESTAMPTZ NOT NULL,
    duration_minutes INT NOT NULL DEFAULT 60,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    
    location TEXT, -- Physical address or 'Remote'
    video_url TEXT, -- External link (Zoom/Meet) or 'internal' for LiveKit
    
    candidate_response TEXT NOT NULL DEFAULT 'pending' CHECK (candidate_response IN ('pending', 'accepted', 'declined', 'proposed_reschedule')),
    proposed_times JSONB DEFAULT '[]'::jsonb, -- List of alt times: [{"date": "...", "reason": "..."}]
    
    company_notes TEXT, -- Private to recruiters
    candidate_instructions TEXT, -- Visible to candidate
    
    created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Interview Participants
CREATE TABLE public.interview_participants (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE NOT NULL,
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    role TEXT NOT NULL DEFAULT 'interviewer' CHECK (role IN ('interviewer', 'candidate', 'observer')),
    is_primary BOOLEAN DEFAULT false,
    joined_at TIMESTAMPTZ,
    UNIQUE(interview_id, profile_id)
);

-- 4. Video Sessions (LiveKit Integration)
CREATE TABLE public.interview_video_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE UNIQUE NOT NULL,
    room_name TEXT UNIQUE NOT NULL,
    recording_url TEXT,
    transcript TEXT,
    ai_summary JSONB DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Coding Sessions (Piston Sandbox & Shared Editor)
CREATE TABLE public.interview_coding_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE UNIQUE NOT NULL,
    language TEXT NOT NULL DEFAULT 'javascript',
    problem_statement TEXT,
    starter_code TEXT,
    final_code TEXT,
    execution_results JSONB DEFAULT '[]'::jsonb, -- History of Piston runs
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Feedback Templates (Company-specific)
CREATE TABLE public.interview_feedback_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    criteria JSONB NOT NULL, -- [{"name": "Technical Depth", "weight": 0.4}, ...]
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Interview Feedback (Evaluation results)
CREATE TABLE public.interview_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE NOT NULL,
    interviewer_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    template_id UUID REFERENCES public.interview_feedback_templates(id) ON DELETE SET NULL,
    
    overall_score NUMERIC CHECK (overall_score >= 1 AND overall_score <= 5),
    scores_json JSONB NOT NULL DEFAULT '{}'::jsonb, -- {"criterion_id": score, ...}
    recommendation TEXT CHECK (recommendation IN ('strong_hire', 'hire', 'no_hire', 'strong_no_hire', 'uncertain')),
    comments TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(interview_id, interviewer_id)
);

-- 8. Practice Sessions (Autonomous training for candidates)
CREATE TABLE public.interview_practice_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    
    difficulty TEXT NOT NULL CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    focus_areas TEXT[] DEFAULT '{}'::text[],
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    
    overall_score NUMERIC,
    ai_report JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- 9. Practice Questions
CREATE TABLE public.practice_questions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID REFERENCES public.interview_practice_sessions(id) ON DELETE CASCADE NOT NULL,
    prompt TEXT NOT NULL,
    category TEXT,
    
    answer_transcript TEXT,
    audio_url TEXT,
    video_url TEXT,
    
    ai_feedback JSONB DEFAULT '{}'::jsonb, -- {"score": 85, "points": ["..."], "improvements": ["..."]}
    score NUMERIC,
    
    order_index INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 10. Activity Logs (Audit Trail)
CREATE TABLE public.interview_activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    interview_id UUID REFERENCES public.interviews(id) ON DELETE CASCADE NOT NULL,
    actor_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL, -- 'scheduled', 'rescheduled', 'cancelled', 'completed', 'feedback_submitted'
    notes TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Security: RLS Policies
-- ============================================================

ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_video_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_coding_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_feedback_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_practice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.practice_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_activity_logs ENABLE ROW LEVEL SECURITY;

-- Interviews: Participants and associated company can view
CREATE POLICY "Participants and hiring teams can view interviews." ON public.interviews
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.interview_participants 
            WHERE interview_id = public.interviews.id AND profile_id = auth.uid()
        ) OR 
        EXISTS (
            SELECT 1 FROM public.job_applications ja
            JOIN public.jobs j ON ja.job_id = j.id
            WHERE ja.id = public.interviews.application_id AND j.company_id = auth.uid()
        )
    );

-- Participants: Viewable by anyone in the interview
CREATE POLICY "Participants in the same interview can view each other." ON public.interview_participants
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.interview_participants ip
            WHERE ip.interview_id = public.interview_participants.interview_id AND ip.profile_id = auth.uid()
        )
    );

-- Feedback: Interviewers see all for their session, candidates see ONLY if released (not in schema yet, but for now recruiters only)
CREATE POLICY "Recruiters can manage feedback." ON public.interview_feedback
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.interviews i
            JOIN public.job_applications ja ON i.application_id = ja.id
            JOIN public.jobs j ON ja.job_id = j.id
            WHERE i.id = public.interview_feedback.interview_id AND j.company_id = auth.uid()
        )
    );

-- Practice Sessions: Candidate only
CREATE POLICY "Candidates manage their own practice sessions." ON public.interview_practice_sessions
    FOR ALL USING (auth.uid() = candidate_id);

CREATE POLICY "Candidates manage their own practice questions." ON public.practice_questions
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.interview_practice_sessions 
            WHERE id = session_id AND candidate_id = auth.uid()
        )
    );

-- ============================================================
-- Triggers: updated_at & Activity Logging
-- ============================================================

-- Function to log interview activities automatically
CREATE OR REPLACE FUNCTION log_interview_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        IF (OLD.status <> NEW.status) THEN
            INSERT INTO public.interview_activity_logs (interview_id, actor_id, action, notes)
            VALUES (NEW.id, auth.uid(), 'status_change', 'Status changed from ' || OLD.status || ' to ' || NEW.status);
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_interview_status_change
    AFTER UPDATE ON public.interviews
    FOR EACH ROW EXECUTE FUNCTION log_interview_activity();

-- Standard updated_at triggers
CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON public.interviews FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_coding_sessions_updated_at BEFORE UPDATE ON public.interview_coding_sessions FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_feedback_updated_at BEFORE UPDATE ON public.interview_feedback FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- ============================================================
-- Realtime: Enable Replication
-- ============================================================

ALTER PUBLICATION supabase_realtime ADD TABLE public.interview_coding_sessions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.interview_participants;
ALTER PUBLICATION supabase_realtime ADD TABLE public.interviews;
