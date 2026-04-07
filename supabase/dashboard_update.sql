-- 1. Extend Profiles for recruiters and better candidate context
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS company_name TEXT,
ADD COLUMN IF NOT EXISTS industry TEXT,
ADD COLUMN IF NOT EXISTS headline TEXT;

-- 2. Create Interviews Table
CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE NOT NULL,
    candidate_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    interviewer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location TEXT, -- Meeting link or address
    type TEXT CHECK (type IN ('virtual', 'on-site', 'phone')) DEFAULT 'virtual',
    status TEXT CHECK (status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')) DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for Interviews
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own interviews." ON public.interviews
    FOR SELECT USING (auth.uid() = candidate_id OR auth.uid() = interviewer_id OR EXISTS (
        SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()
    ));

CREATE POLICY "Companies can manage interviews for their jobs." ON public.interviews
    FOR ALL USING (EXISTS (
        SELECT 1 FROM public.jobs WHERE id = job_id AND company_id = auth.uid()
    ));

-- 3. Create Profile Analytics (for Views)
CREATE TABLE IF NOT EXISTS public.profile_views (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    viewer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    viewer_ip TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for Profile Views
ALTER TABLE public.profile_views ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile analytics." ON public.profile_views
    FOR SELECT USING (auth.uid() = profile_id);

CREATE POLICY "Public view tracking." ON public.profile_views
    FOR INSERT WITH CHECK (true);

-- 4. Update Trigger for Interviews
CREATE TRIGGER update_interviews_updated_at BEFORE UPDATE ON public.interviews FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
