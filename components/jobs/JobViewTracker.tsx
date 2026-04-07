"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase/client";

interface JobViewTrackerProps {
  jobId: string;
}

export default function JobViewTracker({ jobId }: JobViewTrackerProps) {
  const supabase = createClient();

  useEffect(() => {
    const trackView = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      
      // We don't block on errors here as tracking is secondary to UI
      await supabase
        .from("job_views")
        .insert({
          job_id: jobId,
          user_id: user?.id || null,
          user_agent: typeof window !== "undefined" ? window.navigator.userAgent : null,
        });
    };

    // Track after a small delay to ensure it's a real view
    const timer = setTimeout(trackView, 2000);
    return () => clearTimeout(timer);
  }, [jobId, supabase]);

  return null; // Invisible component
}
