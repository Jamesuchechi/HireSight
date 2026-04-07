"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    FileText, Search, Filter, ChevronRight, 
    Clock, CheckCircle2, XCircle, 
    TrendingUp, MousePointer2, Users,
    ArrowUpRight, Mail
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";

export default function RecruiterApplications() {
    const supabase = createClient();
    const [applications, setApplications] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [filterStatus, setFilterStatus] = useState("all");

    useEffect(() => {
        const fetchApplications = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Fetch applications for all jobs belonging to this recruiter
            const { data } = await supabase
                .from("job_applications")
                .select(`
                    *,
                    job:jobs!inner(title, company_id),
                    candidate:profiles(full_name, avatar_url, headline)
                `)
                .eq("job.company_id", user.id)
                .order("created_at", { ascending: false });

            if (data) setApplications(data);
            setLoading(false);
        };

        fetchApplications();
    }, [supabase]);

    const filteredApps = applications.filter(app => {
        const matchesSearch = app.job.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                             app.candidate?.full_name?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = filterStatus === "all" || app.status === filterStatus;
        return matchesSearch && matchesStatus;
    });

    const stats = {
        total: applications.length,
        screening: applications.filter(a => a.status === "screening").length,
        interviews: applications.filter(a => a.status === "interview").length,
        hired: applications.filter(a => a.status === "hired").length
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-secondary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="space-y-10">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div className="space-y-2">
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Application <span className="text-secondary tracking-normal">Matrix</span>
                    </h1>
                    <p className="text-gray-500 font-bold">You are presiding over <span className="text-secondary italic font-black">{applications.length} active</span> talent deployments.</p>
                </div>
            </header>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Incoming" value={stats.total} icon={<Users />} color="text-zinc-900" bg="bg-gray-100" />
                <StatCard title="In Screening" value={stats.screening} icon={<MousePointer2 />} color="text-primary" bg="bg-primary/5" />
                <StatCard title="Interviews" value={stats.interviews} icon={<TrendingUp />} color="text-secondary" bg="bg-secondary/5" />
                <StatCard title="Successful Hires" value={stats.hired} icon={<CheckCircle2 />} color="text-emerald-500" bg="bg-emerald-50" />
            </div>

            {/* Search & Filter */}
            <div className="flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-secondary transition-colors" />
                    <input 
                        type="text"
                        placeholder="Search candidates or job titles..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-16 pr-6 py-4 bg-white border border-gray-100 rounded-[24px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-secondary/5 transition-all shadow-sm"
                    />
                </div>
                <div className="flex items-center space-x-2">
                    {["all", "applied", "screening", "interview", "offer", "hired", "rejected"].map((s) => (
                        <button
                            key={s}
                            onClick={() => setFilterStatus(s)}
                            className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                                filterStatus === s 
                                ? "bg-zinc-900 text-white" 
                                : "bg-white border border-gray-100 text-gray-400 hover:bg-gray-50"
                            }`}
                        >
                            {s}
                        </button>
                    ))}
                </div>
            </div>

            {/* Applications List */}
            {filteredApps.length > 0 ? (
                <div className="space-y-4">
                    {filteredApps.map((app) => (
                        <ApplicationRow key={app.id} app={app} />
                    ))}
                </div>
            ) : (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[40px] p-20 text-center space-y-6">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-300">
                        <Users className="w-10 h-10" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-black text-zinc-900 italic tracking-tight mb-2">Matrix Empty</h3>
                        <p className="text-gray-500 font-bold max-w-sm mx-auto">
                            {searchQuery ? "No applications match your current search parameters." : "No talent has initiated contact for your jobs yet."}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

function ApplicationRow({ app }: { app: any }) {
    const statusConfig: Record<string, { color: string, bg: string, icon: any }> = {
        applied: { color: "text-blue-500", bg: "bg-blue-50", icon: <Clock className="w-4 h-4" /> },
        screening: { color: "text-primary", bg: "bg-primary/10", icon: <MousePointer2 className="w-4 h-4" /> },
        interview: { color: "text-secondary", bg: "bg-secondary/10", icon: <TrendingUp className="w-4 h-4" /> },
        offer: { color: "text-emerald-500", bg: "bg-emerald-50", icon: <CheckCircle2 className="w-4 h-4" /> },
        hired: { color: "text-emerald-600", bg: "bg-emerald-100", icon: <CheckCircle2 className="w-4 h-4" /> },
        rejected: { color: "text-red-500", bg: "bg-red-50", icon: <XCircle className="w-4 h-4" /> }
    };

    const config = statusConfig[app.status] || statusConfig.applied;

    return (
        <div className="group bg-white border border-gray-100 rounded-[32px] p-6 hover:shadow-xl hover:border-secondary/20 transition-all">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gray-50 rounded-[24px] border border-gray-100 flex items-center justify-center font-black text-secondary italic overflow-hidden">
                        {app.candidate?.avatar_url ? (
                            <img src={app.candidate.avatar_url} className="w-full h-full object-cover" alt="" />
                        ) : (
                            <span className="text-xl">{app.candidate?.full_name?.[0]}</span>
                        )}
                    </div>
                    <div>
                        <h4 className="text-lg font-black text-zinc-900 italic tracking-tight">{app.candidate?.full_name}</h4>
                        <div className="flex items-center space-x-3 mt-1">
                            <span className="text-xs font-bold text-primary italic uppercase tracking-widest">{app.job.title}</span>
                            <div className="w-1 h-1 rounded-full bg-gray-200" />
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">{app.candidate?.headline || "Elite Talent"}</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center space-x-8">
                    <div className="text-right">
                        <div className="text-2xl font-black text-primary italic leading-none mb-1">{app.match_score || 0}%</div>
                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest">Neural Match</p>
                    </div>

                    <div className="hidden lg:block text-right">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">Received</p>
                        <p className="text-xs font-bold text-zinc-900">{formatDistanceToNow(new Date(app.created_at))} ago</p>
                    </div>
                    
                    <div className={`px-5 py-2.5 rounded-2xl flex items-center space-x-2 ${config.bg} ${config.color}`}>
                        {config.icon}
                        <span className="text-[10px] font-black uppercase tracking-[0.2em]">{app.status}</span>
                    </div>

                    <div className="flex items-center space-x-2">
                        <Link 
                            href={`/dashboard/applications/review/${app.id}`}
                            className="p-3 bg-gray-50 text-gray-400 hover:bg-zinc-900 hover:text-white rounded-xl transition-all"
                        >
                            <ArrowUpRight className="w-4 h-4" />
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, icon, color, bg }: any) {
    return (
        <div className="bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm hover:shadow-md transition-all group overflow-hidden relative text-center items-center flex flex-col">
            <div className={`p-4 rounded-2xl ${bg} ${color} inline-flex items-center justify-center mb-6`}>
                {icon}
            </div>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{title}</p>
            <h4 className="text-3xl font-black text-zinc-900 italic">{value}</h4>
        </div>
    );
}
