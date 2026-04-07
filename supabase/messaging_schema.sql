-- Elite Messaging Hub Schema

-- 1. Conversations Table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject TEXT,
    job_id UUID REFERENCES public.jobs(id) ON DELETE SET NULL,
    application_id UUID REFERENCES public.job_applications(id) ON DELETE SET NULL,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 2. Participants Junction Table
CREATE TABLE public.conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    last_read_at TIMESTAMPTZ DEFAULT now(),
    joined_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE(conversation_id, user_id)
);

-- 3. Messages Table
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    message_type TEXT CHECK (message_type IN ('user', 'system', 'template')) DEFAULT 'user',
    is_edited BOOLEAN DEFAULT false,
    edited_at TIMESTAMPTZ,
    is_deleted BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 4. Message Attachments
CREATE TABLE public.message_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES public.messages(id) ON DELETE CASCADE,
    file_url TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT,
    file_size INT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 5. Message Templates (Recruiter Focus)
CREATE TABLE public.message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    subject TEXT,
    content TEXT NOT NULL,
    category TEXT CHECK (category IN ('screening', 'interview', 'rejection', 'offer', 'general')) DEFAULT 'general',
    usage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- 6. Blocked Users
CREATE TABLE public.blocked_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blocker_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    blocked_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    UNIQUE(blocker_id, blocked_id)
);

-- Enable RLS
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blocked_users ENABLE ROW LEVEL SECURITY;

-- RLS Policies

-- Participants can see their own memberships
CREATE POLICY "Users can view their conversation participations" 
ON public.conversation_participants FOR SELECT 
USING (auth.uid() = user_id);

-- Conversations are visible only to participants
CREATE POLICY "Users can view conversations they are part of"
ON public.conversations FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.conversation_participants 
        WHERE conversation_id = conversations.id 
        AND user_id = auth.uid()
    )
);

-- Messages are visible to conversation participants
CREATE POLICY "Users can view messages in their conversations"
ON public.messages FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.conversation_participants 
        WHERE conversation_id = messages.conversation_id 
        AND user_id = auth.uid()
    )
);

-- Insertion: Participants can send messages to their conversations
CREATE POLICY "Users can send messages to their conversations"
ON public.messages FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.conversation_participants 
        WHERE conversation_id = messages.conversation_id 
        AND user_id = auth.uid()
    )
    AND sender_id = auth.uid()
);

-- Templates are private to the creator
CREATE POLICY "Users can manage their own templates"
ON public.message_templates FOR ALL
USING (auth.uid() = user_id);

-- Realtime Configuration
-- Note: Enable publication for these tables in Supabase Dashboard
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;
-- ALTER PUBLICATION supabase_realtime ADD TABLE public.conversations;

-- 7. Supabase Storage Policies (message-attachments bucket)
-- Note: These policies reside in the 'storage' schema
INSERT INTO storage.buckets (id, name, public) VALUES ('message-attachments', 'message-attachments', false) ON CONFLICT DO NOTHING;

CREATE POLICY "Participants can upload attachments"
ON storage.objects FOR INSERT
TO authenticated
WITH CHECK (
    bucket_id = 'message-attachments' AND
    (storage.foldername(name))[1] IN (
        SELECT m.id::text FROM public.messages m
        JOIN public.conversation_participants cp ON cp.conversation_id = m.conversation_id
        WHERE cp.user_id = auth.uid()
    )
);

CREATE POLICY "Participants can view attachments"
ON storage.objects FOR SELECT
TO authenticated
USING (
    bucket_id = 'message-attachments' AND
    (storage.foldername(name))[1] IN (
        SELECT m.id::text FROM public.messages m
        JOIN public.conversation_participants cp ON cp.conversation_id = m.conversation_id
        WHERE cp.user_id = auth.uid()
    )
);

-- Triggers for updated_at
CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON public.conversations FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_message_templates_updated_at BEFORE UPDATE ON public.message_templates FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- 8. Unread Message Count Helper
CREATE OR REPLACE FUNCTION get_unread_message_count(uid UUID)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)::INTEGER 
        FROM public.messages m
        JOIN public.conversation_participants cp ON cp.conversation_id = m.conversation_id
        WHERE cp.user_id = uid
        AND m.sender_id != uid
        AND m.created_at > cp.last_read_at
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Profile Discovery for Messaging
-- Allow all authenticated users to see basic profile info for messaging search
CREATE POLICY "Public profile discovery for messages"
ON public.profiles FOR SELECT
TO authenticated
USING (true);
