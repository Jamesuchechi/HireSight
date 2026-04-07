-- ============================================================
-- HireSight: Notification System Schema
-- Run this in the Supabase SQL Editor
-- ============================================================

-- 1. Notifications Table
CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'system' CHECK (type IN (
        'application_received',
        'application_status_changed',
        'new_message',
        'new_follower',
        'new_job_from_follow',
        'interview_scheduled',
        'screening_completed',
        'job_expiring',
        'profile_viewed',
        'assessment_passed',
        'system'
    )),
    action_url TEXT,
    action_text TEXT,
    is_read BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Enable RLS
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- 3. RLS Policies
CREATE POLICY "Users can view their own notifications."
    ON public.notifications FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own notifications."
    ON public.notifications FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notifications."
    ON public.notifications FOR DELETE USING (auth.uid() = user_id);

-- System/API routes can insert for any user (service role bypasses RLS anyway,
-- but this allows authenticated inserts from server actions too)
CREATE POLICY "Authenticated users can insert notifications."
    ON public.notifications FOR INSERT WITH CHECK (true);

-- 4. Enable Realtime (so the bell icon updates live without polling)
ALTER PUBLICATION supabase_realtime ADD TABLE public.notifications;

-- 5. Notification Preferences Table
CREATE TABLE public.notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES public.profiles(id) ON DELETE CASCADE,
    email_frequency TEXT NOT NULL DEFAULT 'instant'
        CHECK (email_frequency IN ('instant', 'daily', 'weekly', 'off')),
    notify_applications BOOLEAN NOT NULL DEFAULT true,
    notify_messages BOOLEAN NOT NULL DEFAULT true,
    notify_jobs BOOLEAN NOT NULL DEFAULT true,
    notify_assessments BOOLEAN NOT NULL DEFAULT true,
    notify_system BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage their own preferences."
    ON public.notification_preferences FOR ALL USING (auth.uid() = user_id);

-- 6. Index for performance
CREATE INDEX idx_notifications_user_id_created ON public.notifications (user_id, created_at DESC);
CREATE INDEX idx_notifications_user_id_is_read ON public.notifications (user_id, is_read);
