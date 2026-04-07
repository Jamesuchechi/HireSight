-- Analytics Subsystem Schema

-- 1. Create Page Views Tracking
CREATE TABLE public.page_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    viewer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL, -- Null if anonymous
    target_type TEXT NOT NULL CHECK (target_type IN ('job', 'profile')),
    target_id UUID NOT NULL, -- Logical reference depending on type
    viewer_ip TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 1b. Application Status History (to track conversion speed)
CREATE TABLE public.application_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Create Search Queries Tracking
CREATE TABLE public.search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    query_text TEXT NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb,
    results_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Indexes for Analytics Scale
CREATE INDEX idx_page_views_target ON public.page_views (target_type, target_id, created_at DESC);
CREATE INDEX idx_page_views_viewer ON public.page_views (viewer_id, created_at DESC);
CREATE INDEX idx_search_queries_created ON public.search_queries (created_at DESC);

-- 4. Enable RLS
ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.search_queries ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies
-- Anyone can insert a page view (even anonymous)
CREATE POLICY "Anyone can insert page views" ON public.page_views
    FOR INSERT WITH CHECK (true);

-- Companies can view page views for their own jobs
CREATE POLICY "Companies can view job views" ON public.page_views
    FOR SELECT USING (
        target_type = 'job' AND target_id IN (
            SELECT id FROM public.jobs WHERE company_id = auth.uid()
        )
    );

-- Users can view page views on their own profile
CREATE POLICY "Users can view their profile views" ON public.page_views
    FOR SELECT USING (
        target_type = 'profile' AND target_id = auth.uid()
    );

-- Search queries can be inserted by anyone
CREATE POLICY "Anyone can insert search queries" ON public.search_queries
    FOR INSERT WITH CHECK (true);

-- Users can select their own search queries
CREATE POLICY "Users can view own search queries" ON public.search_queries
    FOR SELECT USING (user_id = auth.uid());

-- Users can view status history
ALTER TABLE public.application_status_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view status history" ON public.application_status_history
    FOR SELECT USING (
        application_id IN (
            SELECT id FROM public.job_applications WHERE candidate_id = auth.uid()
            OR job_id IN (SELECT id FROM public.jobs WHERE company_id = auth.uid())
        )
    );
CREATE POLICY "System can insert status history" ON public.application_status_history
    FOR INSERT WITH CHECK (true);



-- 6. High-Performance RPC Aggregations

-- 6a. Get Company Funnel & Overview Metrics
CREATE OR REPLACE FUNCTION get_company_recruitment_metrics(cid UUID)
RETURNS JSONB AS $$
DECLARE
    total_jobs INT;
    total_applications INT;
    new_today INT;
    hires INT;
    avg_score FLOAT;
    avg_resp FLOAT;
BEGIN
    SELECT COUNT(*) INTO total_jobs FROM public.jobs WHERE company_id = cid;
    
    SELECT COUNT(*), 
           COUNT(*) FILTER (WHERE created_at >= current_date),
           COUNT(*) FILTER (WHERE status = 'hired'),
           AVG(match_score)
    INTO total_applications, new_today, hires, avg_score
    FROM public.job_applications 
    WHERE job_id IN (SELECT id FROM public.jobs WHERE company_id = cid);

    -- Calculate Avg Response Time in days (applied to first status change)
    SELECT AVG(EXTRACT(EPOCH FROM (h.created_at - a.created_at))/86400)
    INTO avg_resp
    FROM public.job_applications a
    JOIN public.application_status_history h ON a.id = h.application_id
    WHERE a.job_id IN (SELECT id FROM public.jobs WHERE company_id = cid)
    AND h.old_status = 'applied';
    
    RETURN jsonb_build_object(
        'total_jobs', COALESCE(total_jobs, 0),
        'total_applications', COALESCE(total_applications, 0),
        'new_applications_today', COALESCE(new_today, 0),
        'total_hires', COALESCE(hires, 0),
        'average_match_score', COALESCE(avg_score, 0),
        'avg_response_time', ROUND(COALESCE(avg_resp, 0)::NUMERIC, 1),
        'cost_per_hire', (total_jobs * 250) + (total_applications * 5) -- Logic to be replaced with real budget later
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 6b. Get Candidate Overview Metrics
CREATE OR REPLACE FUNCTION get_candidate_metrics(cid UUID)
RETURNS JSONB AS $$
DECLARE
    total_applications INT;
    applications_pending INT;
    applications_interview INT;
    total_offers INT;
    profile_views INT;
BEGIN
    SELECT COUNT(*),
           COUNT(*) FILTER (WHERE status = 'applied'),
           COUNT(*) FILTER (WHERE status = 'interview'),
           COUNT(*) FILTER (WHERE status IN ('offer', 'hired'))
    INTO total_applications, applications_pending, applications_interview, total_offers
    FROM public.job_applications WHERE candidate_id = cid;

    SELECT COUNT(*) INTO profile_views 
    FROM public.page_views 
    WHERE target_type = 'profile' AND target_id = cid;

    RETURN jsonb_build_object(
        'total_applications', COALESCE(total_applications, 0),
        'pending', COALESCE(applications_pending, 0),
        'interviews', COALESCE(applications_interview, 0),
        'offers_received', COALESCE(total_offers, 0),
        'profile_views', COALESCE(profile_views, 0)
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 6c. Get Job Specific Analytics
CREATE OR REPLACE FUNCTION get_job_analytics(jid UUID)
RETURNS JSONB AS $$
DECLARE
    total_views INT;
    total_apps INT;
    apps_today INT;
    funnel RECORD;
BEGIN
    SELECT COUNT(*) INTO total_views FROM public.page_views WHERE target_type = 'job' AND target_id = jid;
    SELECT COUNT(*), COUNT(*) FILTER (WHERE created_at >= current_date) INTO total_apps, apps_today FROM public.job_applications WHERE job_id = jid;

    -- Funnel Breakdown
    SELECT 
        COUNT(*) FILTER (WHERE status = 'screening') as screening,
        COUNT(*) FILTER (WHERE status = 'interview') as interviews,
        COUNT(*) FILTER (WHERE status IN ('offer', 'hired')) as offers
    INTO funnel
    FROM public.job_applications WHERE job_id = jid;

    RETURN jsonb_build_object(
        'views', COALESCE(total_views, 0),
        'total_applications', COALESCE(total_apps, 0),
        'applications_today', COALESCE(apps_today, 0),
        'conversion_rate', CASE WHEN total_views > 0 THEN (total_apps::FLOAT / total_views::FLOAT) * 100 ELSE 0 END,
        'funnel', jsonb_build_object(
            'applied', COALESCE(total_apps, 0),
            'screening', COALESCE(funnel.screening, 0),
            'interviews', COALESCE(funnel.interviews, 0),
            'offers', COALESCE(funnel.offers, 0)
        )
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 6d. Get Skill Intelligence (Behavioral & Advanced)
CREATE OR REPLACE FUNCTION get_skill_intelligence(cid UUID)
RETURNS JSONB AS $$
DECLARE
    total_taken INT;
    avg_score FLOAT;
    consistency FLOAT;
BEGIN
    SELECT COUNT(*), AVG(score) INTO total_taken, avg_score FROM public.skill_test_results WHERE profile_id = cid;
    
    -- Variance calculation for consistency score
    SELECT COALESCE(100 - STDDEV(score), 100) INTO consistency FROM public.skill_test_results WHERE profile_id = cid;

    RETURN jsonb_build_object(
        'assessments_taken', COALESCE(total_taken, 0),
        'average_score', COALESCE(avg_score, 0),
        'consistency_score', LEAST(100, GREATEST(0, COALESCE(consistency, 100))),
        'improvement_rate', 12.5 -- Mocked for now until more data
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- 6e. Calculate Profile Completion
CREATE OR REPLACE FUNCTION calculate_profile_completion(pid UUID)
RETURNS INTEGER AS $$
DECLARE
    score INTEGER := 0;
    prof RECORD;
BEGIN
    SELECT * INTO prof FROM public.profiles WHERE id = pid;
    
    IF prof.full_name IS NOT NULL AND prof.full_name != '' THEN score := score + 20; END IF;
    IF prof.bio IS NOT NULL AND prof.bio != '' THEN score := score + 20; END IF;
    IF prof.avatar_url IS NOT NULL AND prof.avatar_url != '' THEN score := score + 20; END IF;
    
    -- Check JSONB arrays (skills, experience)
    IF prof.skills IS NOT NULL AND jsonb_array_length(prof.skills) > 0 THEN score := score + 20; END IF;
    IF prof.experience IS NOT NULL AND jsonb_array_length(prof.experience) > 0 THEN score := score + 20; END IF;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

