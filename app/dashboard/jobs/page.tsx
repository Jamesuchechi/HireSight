"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Database } from "@/types/database";
import RecruiterJobCard from "@/components/jobs/RecruiterJobCard";
import { useRouter } from "next/navigation";
import { Plus, Search, Filter, Rocket, Briefcase, Users, Eye, TrendingUp } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

type Job = Database["public"]["Tables"]["jobs"]["Row"];

export default function RecruiterJobsPage() {
    const router = useRouter();
    const supabase = createClient();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    const [stats, setStats] = useState({
        active: 0,
        totalApplicants: 0,
        totalViews: 0,
        hiringRate: "0%"
    });

    useEffect(() => {
        const fetchJobs = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Fetch jobs with application and view counts
            const { data, error } = await supabase
                .from("jobs")
                .select(`
                    *,
                    applications:job_applications(count),
                    views:job_views(count)
                `)
                .eq("company_id", user.id)
                .order("created_at", { ascending: false });

            if (!error && data) {
                // Cast because Supabase returns counts as an array of objects
                const processedJobs = data.map(job => ({
                    ...job,
                    applicant_count: (job.applications as any)[0]?.count || 0,
                    view_count: (job.views as any)[0]?.count || 0
                }));
                
                setJobs(processedJobs as any);

                // Aggregate stats
                const totalApps = processedJobs.reduce((acc, job) => acc + job.applicant_count, 0);
                const totalViews = processedJobs.reduce((acc, job) => acc + job.view_count, 0);
                const activeCount = processedJobs.filter(j => j.status === 'active').length;

                setStats({
                    active: activeCount,
                    totalApplicants: totalApps,
                    totalViews: totalViews,
                    hiringRate: totalApps > 0 ? `${((processedJobs.filter(j => j.status === 'closed').length / totalApps) * 100).toFixed(1)}%` : "0%"
                });
            }

            // Role Protection
            const { data: profile } = await supabase.from("profiles").select("role").eq("id", user.id).single();
            if (profile?.role === "candidate") {
                router.push("/jobs");
                return;
            }

            setLoading(false);
        };

        fetchJobs();
    }, [supabase]);

    const filteredJobs = jobs.filter(job => 
        job.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.location?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between space-y-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 mb-2 italic tracking-tighter">
                        Manage <span className="text-primary tracking-normal">Opportunities</span>
                    </h1>
                    <p className="text-gray-500 font-bold">You have <span className="text-primary italic font-black font-body">{jobs.length} total</span> job postings currently listed.</p>
                </div>
                <Link
                    href="/dashboard/jobs/create"
                    className="inline-flex items-center space-x-2 px-8 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-sm uppercase tracking-widest italic shadow-2xl hover:scale-[1.05] active:scale-[0.95] transition-all group"
                >
                    <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
                    <span>Post New Job</span>
                </Link>
            </header>

            {/* Stats Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="p-6 bg-white border border-gray-100 rounded-[32px] shadow-sm">
                    <div className="p-3 rounded-2xl bg-primary/10 text-primary inline-flex mb-4">
                        <Briefcase className="w-5 h-5" />
                    </div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Active Positions</p>
                    <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{jobs.filter(j => j.status === 'active').length}</h4>
                </div>
                <div className="p-6 bg-white border border-gray-100 rounded-[32px] shadow-sm">
                    <div className="p-3 rounded-2xl bg-secondary/10 text-secondary inline-flex mb-4">
                        <Users className="w-5 h-5" />
                    </div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Total Applicants</p>
                    <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{stats.totalApplicants}</h4>
                </div>
                <div className="p-6 bg-white border border-gray-100 rounded-[32px] shadow-sm">
                    <div className="p-3 rounded-2xl bg-accent/10 text-accent inline-flex mb-4">
                        <Eye className="w-5 h-5" />
                    </div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Total Job Views</p>
                    <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{stats.totalViews >= 1000 ? `${(stats.totalViews / 1000).toFixed(1)}k` : stats.totalViews}</h4>
                </div>
                <div className="p-6 bg-white border border-gray-100 rounded-[32px] shadow-sm">
                    <div className="p-3 rounded-2xl bg-emerald-100 text-emerald-600 inline-flex mb-4">
                        <TrendingUp className="w-5 h-5" />
                    </div>
                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Hiring Rate</p>
                    <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{stats.hiringRate}</h4>
                </div>
            </div>

            {/* Search & Filter Bar */}
            <div className="flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 group">
                    <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-primary transition-colors" />
                    <input 
                        type="text"
                        placeholder="Search jobs by title or location..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-14 pr-6 py-4 bg-white border border-gray-100 rounded-[24px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all"
                    />
                </div>
                <button className="flex items-center space-x-2 px-6 py-4 bg-white border border-gray-100 rounded-[24px] font-black text-xs uppercase tracking-widest text-gray-500 hover:bg-gray-50 transition-all">
                    <Filter className="w-4 h-4" />
                    <span>Filter</span>
                </button>
            </div>

            {/* Jobs Grid */}
            {filteredJobs.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredJobs.map((job) => (
                        <RecruiterJobCard 
                            key={job.id} 
                            job={job} 
                            applicantCount={(job as any).applicant_count}
                            viewCount={(job as any).view_count}
                            onEdit={(id) => router.push(`/dashboard/jobs/${id}/edit`)}
                            onDuplicate={(id) => console.log("Duplicate Protocol", id)}
                            onDelete={(id) => console.log("Aborting Protocol", id)}
                        />
                    ))}
                </div>
            ) : (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[40px] p-20 text-center space-y-6">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto">
                        <Briefcase className="w-10 h-10 text-gray-300" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-black text-zinc-900 italic tracking-tight mb-2">No Job Postings Found</h3>
                        <p className="text-gray-500 font-bold max-w-md mx-auto">
                            {searchQuery ? "We couldn't find any jobs matching your search." : "You haven't posted any jobs yet. Start hiring top talent today!"}
                        </p>
                    </div>
                    {!searchQuery && (
                        <Link 
                            href="/dashboard/jobs/new"
                            className="inline-flex items-center space-x-3 px-8 py-4 bg-primary text-white rounded-2xl font-black text-sm hover:scale-[1.05] transition-all"
                        >
                            <span>Post Your First Job</span>
                            <Rocket className="w-4 h-4" />
                        </Link>
                    )}
                </div>
            )}
        </div>
    );
}
