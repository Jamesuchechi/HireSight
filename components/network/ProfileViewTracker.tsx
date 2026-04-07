"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

interface ProfileViewTrackerProps {
  profileId: string;
}

export default function ProfileViewTracker({ profileId }: ProfileViewTrackerProps) {
  const supabase = createClient();

  useEffect(() => {
    const trackView = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      
      // We don't block on errors here as tracking is secondary to UI
      // Also, don't track if viewing own profile
      if (user && user.id === profileId) {
          return;
      }

      await supabase
        .from("page_views")
        .insert({
          target_type: 'profile',
          target_id: profileId,
          viewer_id: user?.id || null,
          viewer_ip: typeof window !== "undefined" ? window.navigator.userAgent : null,
        });
    };

    // Track after a small delay to ensure it's an intentional view
    const timer = setTimeout(trackView, 3000);
    return () => clearTimeout(timer);
  }, [profileId, supabase]);

  return null; // Invisible tracker
}
