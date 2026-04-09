import { SupabaseClient } from "@supabase/supabase-js";
import { Database } from "@/types/database";

export async function getCandidateDashboardData(supabase: SupabaseClient<Database>, userId: string) {
    // 1. Fetch Profile & Resumes (Separately to avoid join error 400)
    const [profileRes, resumesRes] = await Promise.all([
        supabase
            .from("profiles")
            .select("*")
            .eq("id", userId)
            .single(),
        supabase
            .from("resumes")
            .select("*")
            .eq("user_id", userId)
    ]);

    const profileData = profileRes.data;
    const resumes = resumesRes.data || [];

    const profile = profileData ? { ...profileData, resumes } : null;
    
    // 2. Counts
    const [appsCount, savedCount, viewsCount] = await Promise.all([
        supabase.from("job_applications").select("*", { count: "exact", head: true }).eq("candidate_id", userId),
        supabase.from("saved_jobs").select("*", { count: "exact", head: true }).eq("user_id", userId),
        supabase.from("profile_views").select("*", { count: "exact", head: true }).eq("profile_id", userId)
    ]);

    // 3. Upcoming Interviews
    const { data: interviews } = await supabase
        .from("interviews")
        .select("*, job:jobs(title, location)")
        .eq("candidate_id", userId)
        .gte("start_time", new Date().toISOString())
        .order("start_time", { ascending: true })
        .limit(5);

    // 4. Recent Applications
    const { data: recentApps } = await supabase
        .from("job_applications")
        .select("*, job:jobs(title, location, company_id)")
        .eq("candidate_id", userId)
        .order("created_at", { ascending: false })
        .limit(10);

    // 5. Recommended Jobs (Simplified: Latest active jobs matching candidate interests if available)
    const { data: recommended } = await supabase
        .from("jobs")
        .select("*, company:profiles(full_name, avatar_url, company_name)")
        .eq("status", "active")
        .order("created_at", { ascending: false })
        .limit(5);

    return {
        stats: {
            activeApplications: appsCount.count || 0,
            savedJobs: savedCount.count || 0,
            profileViews: viewsCount.count || 0,
            recommendedCount: recommended?.length || 0
        },
        interviews: interviews || [],
        recentApplications: recentApps || [],
        recommendedJobs: recommended || [],
        profileCompletion: calculateProfileCompletion(profile)
    };
}

export async function getRecruiterDashboardData(supabase: SupabaseClient<Database>, userId: string) {
    // 1. All Non-Deleted Jobs
    const { data: jobs } = await supabase
        .from("jobs")
        .select("id, status")
        .eq("company_id", userId)
        .neq("status", "deleted");

    const jobIds = (jobs as any[])?.map(j => j.id) || [];
    const activeJobs = (jobs as any[])?.filter(j => j.status === 'active') || [];

    // 2. Stats
    // Fix: Count ALL applications for recruiter's jobs, not just those with status 'applied'
    const [applicantsCount, interviewsCount, upcomingInterviews] = await Promise.all([
        supabase.from("job_applications").select("*", { count: "exact", head: true }).in("job_id", jobIds),
        supabase.from("interviews").select("*", { count: "exact", head: true }).in("job_id", jobIds).gte("start_time", new Date().toISOString()),
        supabase.from("interviews").select("*, job:jobs(title, location)").in("job_id", jobIds).gte("start_time", new Date().toISOString()).order("start_time", { ascending: true }).limit(5)
    ]);

    // 3. Top Candidates (Across all jobs, highest match score)
    const { data: topCandidates } = await supabase
        .from("job_applications")
        .select("*, job:jobs(title), candidate:profiles(full_name, avatar_url)")
        .in("job_id", jobIds)
        .order("match_score", { ascending: false })
        .limit(5);

    // 4. Recent Activity (Filtered by company_id correctly)
    const { data: recentActivity } = await supabase
        .from("job_applications")
        .select(`
            *,
            job:jobs!inner(title, company_id),
            candidate:profiles(full_name)
        `)
        .eq("job.company_id", userId)
        .order("created_at", { ascending: false })
        .limit(10);

    // 5. Funnel Stats (Aggregate)
    const { data: funnelData } = await supabase
        .from("job_applications")
        .select("status")
        .in("job_id", jobIds);

    const funnel = {
        applied: (funnelData as any[])?.filter(a => a.status === 'applied').length || 0,
        screening: (funnelData as any[])?.filter(a => a.status === 'screening').length || 0,
        interview: (funnelData as any[])?.filter(a => a.status === 'interview').length || 0,
        offer: (funnelData as any[])?.filter(a => a.status === 'offer').length || 0,
        hired: (funnelData as any[])?.filter(a => a.status === 'hired').length || 0
    };

    return {
        stats: {
            activeJobs: activeJobs.length,
            totalApplicants: applicantsCount.count || 0,
            interviewsThisWeek: interviewsCount.count || 0,
            offersPending: funnel.offer,
            hiredThisMonth: funnel.hired
        },
        topCandidates: topCandidates || [],
        recentActivity: recentActivity || [],
        interviews: upcomingInterviews.data || [],
        funnel
    };
}

function calculateProfileCompletion(profile: Database["public"]["Tables"]["profiles"]["Row"] | any) {
    if (!profile) return 0;
    let score = 0;
    if (profile.avatar_url) score += 10;
    if (profile.full_name) score += 10;
    if (profile.bio) score += 20;
    if (profile.resumes && profile.resumes.some((r: any) => r.is_primary)) score += 30;
    // Add logic for skills if they are stored in a separate table or profile field
    // For now assuming 30% for skills placeholder
    score += (profile.skills_count || 0) >= 5 ? 30 : (profile.skills_count || 0) * 6;
    return Math.min(score, 100);
}
