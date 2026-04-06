-- 1. Create a table for public profiles
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL PRIMARY KEY,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  full_name TEXT,
  role TEXT CHECK (role IN ('candidate', 'recruiter')) DEFAULT 'candidate',
  avatar_url TEXT,
  cover_url TEXT,
  bio TEXT,
  onboarding_completed BOOLEAN DEFAULT false
);

-- 2. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 3. Create RLS Policies
CREATE POLICY "Public profiles are viewable by everyone." ON public.profiles
  FOR SELECT USING (true);

CREATE POLICY "Users can insert their own profile." ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile." ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- 4. Create a function to handle new user signups
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, role, avatar_url)
  VALUES (
    new.id, 
    new.raw_user_meta_data->>'full_name', 
    new.raw_user_meta_data->>'role',
    new.raw_user_meta_data->>'avatar_url'
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 5. Create a trigger to call the function on signup
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 6. Supabase Storage Setup (Manual Action: Create bucket 'profile-assets' first)
-- Enable Storage Policies
CREATE POLICY "Public Access" ON storage.objects
  FOR SELECT USING (bucket_id = 'profile-assets');

CREATE POLICY "Authenticated Upload" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'profile-assets' AND 
    auth.uid() = (storage.foldername(name))[1]::uuid
  );

CREATE POLICY "Authenticated Update" ON storage.objects
  FOR UPDATE USING (
    bucket_id = 'profile-assets' AND 
    auth.uid() = (storage.foldername(name))[1]::uuid
  );

CREATE POLICY "Authenticated Delete" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'profile-assets' AND 
    auth.uid() = (storage.foldername(name))[1]::uuid
  );

-- 7. Resumes Management System
CREATE TABLE public.resumes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  file_url TEXT NOT NULL,
  status TEXT CHECK (status IN ('uploaded', 'parsing', 'parsed', 'failed')) DEFAULT 'uploaded',
  is_primary BOOLEAN DEFAULT false,
  parsed_content JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS for Resumes
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own resumes." ON public.resumes
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resumes." ON public.resumes
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resumes." ON public.resumes
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resumes." ON public.resumes
  FOR DELETE USING (auth.uid() = user_id);

-- 8. Resumes Storage Setup (Manual Action: Create bucket 'resumes' first)
CREATE POLICY "Resumes Read Access" ON storage.objects
  FOR SELECT USING (bucket_id = 'resumes' AND auth.uid() = (storage.foldername(name))[1]::uuid);

CREATE POLICY "Resumes Upload Access" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'resumes' AND 
    auth.uid() = (storage.foldername(name))[1]::uuid
  );

CREATE POLICY "Resumes Delete Access" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'resumes' AND 
    auth.uid() = (storage.foldername(name))[1]::uuid
  );
