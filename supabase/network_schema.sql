-- Network & Following System Schema

-- 1. Create Follows Table
CREATE TABLE public.follows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    follower_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    following_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(follower_id, following_id)
);

-- 2. Create Activities Table
CREATE TABLE public.activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    activity_type TEXT NOT NULL, -- e.g., 'job_posted', 'assessment_passed'
    content JSONB DEFAULT '{}'::jsonb NOT NULL,
    is_public BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Enable Row Level Security (RLS)
ALTER TABLE public.follows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.activities ENABLE ROW LEVEL SECURITY;

-- 4. Follows Policies
-- Everyone can see who follows whom (public social graph)
CREATE POLICY "Follows are viewable by everyone" ON public.follows
    FOR SELECT USING (true);

-- Authenticated users can only insert their own follows
CREATE POLICY "Users can insert their own follows" ON public.follows
    FOR INSERT WITH CHECK (auth.uid() = follower_id);

-- Authenticated users can only delete their own follows
CREATE POLICY "Users can delete their own follows" ON public.follows
    FOR DELETE USING (auth.uid() = follower_id);

-- 5. Activities Policies
-- Everyone can see public activities
CREATE POLICY "Public activities are viewable by everyone" ON public.activities
    FOR SELECT USING (is_public = true);

-- Users can insert their own activities
CREATE POLICY "Users can insert their own activities" ON public.activities
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update/delete their own activities
CREATE POLICY "Users can manage their own activities" ON public.activities
    FOR ALL USING (auth.uid() = user_id);

-- 6. RPC Function for Mutual Followers
CREATE OR REPLACE FUNCTION get_mutual_connections(user_id1 UUID, user_id2 UUID)
RETURNS TABLE (id UUID) AS $$
BEGIN
  RETURN QUERY
  SELECT f1.following_id
  FROM public.follows f1
  JOIN public.follows f2 ON f1.following_id = f2.following_id
  WHERE f1.follower_id = user_id1
    AND f2.follower_id = user_id2;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 7. Indexes for Performance
CREATE INDEX idx_follows_follower ON public.follows (follower_id);
CREATE INDEX idx_follows_following ON public.follows (following_id);
CREATE INDEX idx_activities_user_id ON public.activities (user_id, created_at DESC);
