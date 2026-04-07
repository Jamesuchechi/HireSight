import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import JobAnalytics from "@/components/jobs/JobAnalytics";
import { ChevronLeft, BarChart3, Rocket, Target } from "lucide-react";
import Link from "next/link";
import { Database } from "@/types/database";

export default async function JobAnalyticsPage({ params }: { params: Promise<{ id: string }> }) {
    const supabase = await createClient();
    const { id } = await params;

    // Fetch Job Details
    const { data: job, error: jobError } = await supabase
        .from("jobs")
        .select("*")
        .eq("id", id)
        .single();

    if (jobError || !job) {
        notFound();
    }

    // Fetch Views (Last 14 days)
    const { data: views } = await supabase
        .from("job_views")
        .select("created_at")
        .eq("job_id", id)
        .gte("created_at", new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString());

    // Fetch Applications
    const { data: apps } = await supabase
        .from("job_applications")
        .select("created_at, match_score")
        .eq("job_id", id);

    // Process Data into daily buckets
    const days = Array.from({ length: 14 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() - (13 - i));
        return d.toISOString().split('T')[0];
    });

    const viewsByDate = days.map(date => ({
        date: date.split('-').slice(1).join('/'),
        count: views?.filter(v => v.created_at.startsWith(date)).length || 0
    }));

    const appsByDate = days.map(date => ({
        date: date.split('-').slice(1).join('/'),
        count: apps?.filter(a => a.created_at.startsWith(date)).length || 0
    }));

    const totalViews = views?.length || 0;
    const totalApps = apps?.length || 0;
    const avgMatchScore = apps?.length 
        ? Math.round(apps.reduce((acc, curr) => acc + (curr.match_score || 0), 0) / apps.length) 
        : 0;

    const analyticsData = {
        viewsByDate,
        appsByDate,
        totalViews,
        totalApps,
        avgMatchScore
    };

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20">
            {/* Header */}
            <header className="flex flex-col space-y-6">
                <Link 
                    href="/dashboard/jobs" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Fleet Command</span>
                </Link>

                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-primary/10 text-primary rounded-[20px]">
                                <BarChart3 className="w-6 h-6" />
                            </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">Analytical Matrix</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                            Job <span className="text-primary tracking-normal font-body">Intelligence</span>
                        </h1>
                        <div className="flex items-center space-x-2">
                             <h2 className="text-lg font-bold text-gray-500 italic">{job.title}</h2>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                         <div className="bg-white px-6 py-4 rounded-[24px] border border-gray-100 shadow-sm flex items-center space-x-3">
                             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                             <span className="text-[10px] font-black text-zinc-900 uppercase tracking-widest">Real-time Feed Active</span>
                         </div>
                    </div>
                </div>
            </header>

            {/* Dashboard Content */}
            <JobAnalytics data={analyticsData} />

            {/* Footer Summary */}
            <div className="bg-gradient-to-br from-zinc-900 to-[#121214] rounded-[48px] p-12 flex flex-col md:flex-row items-center justify-between gap-10 overflow-hidden relative group">
                <div className="relative z-10 space-y-4 max-w-xl">
                    <div className="inline-flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full">
                        <Target className="w-3 h-3 text-secondary" />
                        <span className="text-[10px] font-black text-white uppercase tracking-widest">Growth Recommendation</span>
                    </div>
                    <h3 className="text-3xl font-black font-display text-white italic tracking-tight leading-tight">
                        Increase your match score threshold to filter higher-quality applicants.
                    </h3>
                    <p className="text-gray-400 font-bold text-sm leading-relaxed italic">Based on current traffic, a 5% increase in your minimum match score would reduce manual review time by 14 hours per week.</p>
                    <button className="px-8 py-4 bg-white text-zinc-900 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-all">
                        Optimize Threshold
                    </button>
                </div>
                <div className="relative z-10 hidden lg:block">
                     <div className="w-48 h-48 bg-primary/20 blur-[80px] rounded-full" />
                </div>
                {/* Abstract Background Grid */}
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '40px 40px' }} />
            </div>
        </div>
    );
}
