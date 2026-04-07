-- 1. Skill Badges Table
CREATE TABLE public.skill_badges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    assessment_id UUID REFERENCES public.assessments(id) ON DELETE CASCADE NOT NULL,
    attempt_id UUID REFERENCES public.assessment_attempts(id) ON DELETE CASCADE NOT NULL,
    skill_name TEXT NOT NULL,
    badge_level TEXT CHECK (badge_level IN ('bronze', 'silver', 'gold', 'platinum')) DEFAULT 'bronze',
    score NUMERIC NOT NULL,
    verification_code TEXT UNIQUE NOT NULL DEFAULT substring(md5(random()::text), 1, 12),
    is_public BOOLEAN DEFAULT true,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Enable RLS
ALTER TABLE public.skill_badges ENABLE ROW LEVEL SECURITY;

-- 3. POLICIES
CREATE POLICY "Badges are viewable by everyone if public." ON public.skill_badges
    FOR SELECT USING (is_public = true OR auth.uid() = user_id);

CREATE POLICY "System can issue badges." ON public.skill_badges
    FOR INSERT WITH CHECK (auth.uid() = user_id); -- Candidates "claim" their badge upon passing

-- 4. Automatic Profile Skill Verification Trigger
CREATE OR REPLACE FUNCTION public.verify_profile_skill()
RETURNS TRIGGER AS $$
DECLARE
    existing_skills JSONB;
    skill_found BOOLEAN := false;
    new_skills JSONB := '[]'::jsonb;
    skill_entry JSONB;
BEGIN
    -- Get current skills
    SELECT skills INTO existing_skills FROM public.profiles WHERE id = NEW.user_id;
    
    -- Loop through existing skills and update if found
    FOR skill_entry IN SELECT * FROM jsonb_array_elements(existing_skills)
    LOOP
        IF skill_entry->>'name' ILIKE NEW.skill_name THEN
            skill_found := true;
            new_skills := new_skills || skill_entry || jsonb_build_object('is_verified', true, 'badge_id', NEW.id, 'verified_at', NEW.issued_at);
        ELSE
            new_skills := new_skills || skill_entry;
        END IF;
    END LOOP;
    
    -- If skill not in profile, add it as verified
    IF NOT skill_found THEN
        new_skills := new_skills || jsonb_build_object(
            'name', NEW.skill_name,
            'is_verified', true,
            'badge_id', NEW.id,
            'verified_at', NEW.issued_at,
            'level', NEW.badge_level
        );
    END IF;
    
    -- Update profile
    UPDATE public.profiles SET skills = new_skills WHERE id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_badge_issued
    AFTER INSERT ON public.skill_badges
    FOR EACH ROW EXECUTE FUNCTION public.verify_profile_skill();
