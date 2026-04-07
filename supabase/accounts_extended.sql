-- 1. API Keys Table
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_prefix TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    
    CONSTRAINT name_length CHECK (char_length(name) >= 3)
);

-- 2. Notification Preferences Table
CREATE TABLE IF NOT EXISTS public.notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    frequency TEXT CHECK (frequency IN ('instant', 'daily', 'weekly', 'off')) DEFAULT 'instant',
    notify_jobs BOOLEAN DEFAULT true,
    notify_applications BOOLEAN DEFAULT true,
    notify_messages BOOLEAN DEFAULT true,
    notify_views BOOLEAN DEFAULT true,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. RLS for API Keys
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own API keys."
ON public.api_keys FOR ALL
USING (auth.uid() = user_id);

-- 4. RLS for Notification Preferences
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own notification preferences."
ON public.notification_preferences FOR ALL
USING (auth.uid() = user_id);

-- 5. Trigger for New Profile (Auto-create notification preferences)
CREATE OR REPLACE FUNCTION public.handle_new_notification_prefs()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.notification_preferences (user_id)
    VALUES (new.id);
    RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_profile_created_notifications
    AFTER INSERT ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_notification_prefs();

-- 6. Analytics: Ensure profile_views exists and is usable
CREATE TABLE IF NOT EXISTS public.profile_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    viewer_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    viewer_ip TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.profile_views ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile analytics."
ON public.profile_views FOR SELECT
USING (auth.uid() = profile_id);

CREATE POLICY "Anyone can record a profile view."
ON public.profile_views FOR INSERT
WITH CHECK (true);
