-- 1. Extend Jobs Table
ALTER TABLE public.jobs 
ADD COLUMN IF NOT EXISTS responsibilities TEXT,
ADD COLUMN IF NOT EXISTS nice_to_have TEXT,
ADD COLUMN IF NOT EXISTS benefits TEXT,
ADD COLUMN IF NOT EXISTS department TEXT,
ADD COLUMN IF NOT EXISTS salary_period TEXT CHECK (salary_period IN ('hourly', 'monthly', 'yearly')) DEFAULT 'yearly',
ADD COLUMN IF NOT EXISTS positions_available INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS application_deadline TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS requires_cover_letter BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS requires_portfolio BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT false;

-- 2. Extend Job Applications Table
ALTER TABLE public.job_applications 
ADD COLUMN IF NOT EXISTS viewed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS is_shortlisted BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS recruiter_rating INTEGER CHECK (recruiter_rating >= 1 AND recruiter_rating <= 5),
ADD COLUMN IF NOT EXISTS match_details JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS rejection_feedback JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS hired_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS withdrawn_at TIMESTAMP WITH TIME ZONE;

-- 3. Create Application Status History Table
CREATE TABLE IF NOT EXISTS public.application_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Create Application Notes Table
CREATE TABLE IF NOT EXISTS public.application_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES public.job_applications(id) ON DELETE CASCADE NOT NULL,
    author_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    content TEXT NOT NULL,
    is_important BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. RLS for Status History
ALTER TABLE public.application_status_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Companies can view status history for their jobs." ON public.application_status_history
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM public.job_applications ja
        JOIN public.jobs j ON ja.job_id = j.id
        WHERE ja.id = application_id AND j.company_id = auth.uid()
    ));

CREATE POLICY "Candidates can view their own application history." ON public.application_status_history
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM public.job_applications ja
        WHERE ja.id = application_id AND ja.candidate_id = auth.uid()
    ));

-- 6. RLS for Application Notes
ALTER TABLE public.application_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Only companies can interact with application notes." ON public.application_notes
    FOR ALL USING (EXISTS (
        SELECT 1 FROM public.job_applications ja
        JOIN public.jobs j ON ja.job_id = j.id
        WHERE ja.id = application_id AND j.company_id = auth.uid()
    ));

-- 7. Trigger to Record Status Changes
CREATE OR REPLACE FUNCTION public.record_application_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF (OLD.status IS DISTINCT FROM NEW.status) THEN
        INSERT INTO public.application_status_history (application_id, old_status, new_status, changed_by)
        VALUES (NEW.id, OLD.status, NEW.status, auth.uid());
        
        -- Update specific timestamps
        IF (NEW.status = 'hired') THEN
            NEW.hired_at = now();
        ELSIF (NEW.status = 'rejected') THEN
            NEW.rejected_at = now();
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_application_status_update
    BEFORE UPDATE ON public.job_applications
    FOR EACH ROW EXECUTE FUNCTION public.record_application_status_change();
