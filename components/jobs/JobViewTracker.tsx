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
        .from("page_views")
        .insert({
          target_type: 'job',
          target_id: jobId,
          viewer_id: user?.id || null,
          viewer_ip: typeof window !== "undefined" ? window.navigator.userAgent : null, // Using userAgent as proxy for IP since browser cannot easily get IP directly
        });
    };

    // Track after a small delay to ensure it's a real view
    const timer = setTimeout(trackView, 2000);
    return () => clearTimeout(timer);
  }, [jobId, supabase]);

  return null; // Invisible component
}
