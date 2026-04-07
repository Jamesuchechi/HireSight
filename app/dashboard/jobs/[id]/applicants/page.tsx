"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, Users, Filter, Search, 
    LayoutGrid, List, Download, Mail, 
    ArrowRight, Star, Zap, Clock,
    CheckCircle2, XCircle
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import ApplicationKanban from "@/components/jobs/ApplicationKanban";
import { useRouter } from "next/navigation";

export default function JobApplicantsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const supabase = createClient();
    const router = useRouter();
    const [job, setJob] = useState<any>(null);
    const [applicants, setApplicants] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [viewMode, setViewMode] = useState<"kanban" | "table">("kanban");
    const [searchQuery, setSearchQuery] = useState("");

    const fetchApplicants = async () => {
        setLoading(true);
        const { data: jobData } = await supabase
            .from("jobs")
            .select("*")
            .eq("id", id)
            .single();

        const { data: appData, error } = await supabase
            .from("job_applications")
            .select(`
                *,
                candidate:profiles!candidate_id(full_name, avatar_url, bio),
                resume:resumes(title, file_url)
            `)
            .eq("job_id", id)
            .order("match_score", { ascending: false });

        if (jobData) setJob(jobData);
        if (appData) setApplicants(appData);
        setLoading(false);
    };

    useEffect(() => {
        fetchApplicants();
    }, [supabase, id]);

    const handleMove = async (applicationId: string, nextStatus: string) => {
        const app = applicants.find(a => a.id === applicationId);
        if (!app) return;

        const { error } = await supabase
            .from("job_applications")
            .update({ status: nextStatus })
            .eq("id", applicationId);

        if (!error) {
            // Log History
            await supabase
                .from("application_status_history")
                .insert({
                    application_id: applicationId,
                    old_status: app.status,
                    new_status: nextStatus,
                    changed_by: (await supabase.auth.getUser()).data.user?.id,
                    reason: `Moved from ${app.status} to ${nextStatus} via Pipeline.`
                });

            // Optimistic update
            setApplicants(prev => prev.map(a => 
                a.id === applicationId ? { ...a, status: nextStatus } : a
            ));
        }
    };

    const filteredApplicants = applicants.filter(a => 
        a.candidate.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!job) return <div>Job mission not found.</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20">
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
                    <div className="space-y-2">
                        <div className="flex items-center space-x-4">
                             <div className="p-3 bg-primary/10 text-primary rounded-[20px]">
                                 <Users className="w-6 h-6" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">Metric Monitoring</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                            Applicant <span className="text-primary tracking-normal">Intelligence</span>
                        </h1>
                        <h2 className="text-lg font-bold text-gray-500 italic">{job.title}</h2>
                    </div>

                    <div className="flex items-center space-x-2 bg-gray-100 p-1 rounded-2xl">
                        <button 
                            onClick={() => setViewMode("kanban")}
                            className={`p-3 rounded-xl transition-all ${viewMode === "kanban" ? "bg-white text-primary shadow-sm" : "text-gray-400 hover:text-gray-600"}`}
                        >
                            <LayoutGrid className="w-5 h-5" />
                        </button>
                        <button 
                            onClick={() => setViewMode("table")}
                            className={`p-3 rounded-xl transition-all ${viewMode === "table" ? "bg-white text-primary shadow-sm" : "text-gray-400 hover:text-gray-600"}`}
                        >
                            <List className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </header>

            {/* Controls */}
            <div className="flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-primary transition-colors" />
                    <input 
                        type="text"
                        placeholder="Scan metrics for candidate name..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-16 pr-6 py-4 bg-white border border-gray-100 rounded-[28px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all"
                    />
                </div>
                <div className="flex items-center space-x-3">
                    <button className="px-6 py-4 bg-white border border-gray-100 rounded-[24px] font-black text-xs uppercase tracking-widest text-gray-500 flex items-center space-x-2 hover:bg-gray-50">
                        <Filter className="w-4 h-4" />
                        <span>Matrix Filters</span>
                    </button>
                    <button className="px-6 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic flex items-center space-x-2 hover:scale-[1.03] transition-all">
                        <Download className="w-4 h-4" />
                        <span>Export CSV</span>
                    </button>
                </div>
            </div>

            {/* Content Rendering */}
            <AnimatePresence mode="wait">
                {viewMode === "kanban" ? (
                    <motion.div
                        key="kanban"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                    >
                        <ApplicationKanban 
                            applications={filteredApplicants} 
                            onMove={handleMove} 
                        />
                    </motion.div>
                ) : (
                    <motion.div
                        key="table"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="bg-white border border-gray-100 rounded-[48px] overflow-hidden shadow-sm"
                    >
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50 border-b border-gray-100">
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Candidate Metrics</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Stage</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Neural Match</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Applied</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {filteredApplicants.map((a) => (
                                    <tr key={a.id} className="hover:bg-gray-50/30 transition-colors group">
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-4">
                                                <div className="w-12 h-12 bg-gray-50 rounded-2xl border border-gray-100 flex items-center justify-center font-black text-primary italic overflow-hidden">
                                                    {a.candidate.avatar_url ? (
                                                        <img src={a.candidate.avatar_url} className="w-full h-full object-cover" />
                                                    ) : (
                                                        <span>{a.candidate.full_name[0]}</span>
                                                    )}
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-black text-zinc-900 italic tracking-tight">{a.candidate.full_name}</h4>
                                                    <p className="text-[10px] font-bold text-gray-400">{a.resume?.title || "Master Resume"}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="inline-flex px-3 py-1 bg-primary/5 text-primary rounded-lg text-[10px] font-black uppercase tracking-widest border border-primary/10">
                                                {a.status}
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-2 text-primary">
                                                <Zap className="w-4 h-4 animate-pulse" />
                                                <span className="text-sm font-black">{a.match_score || 85}%</span>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6 text-xs text-gray-500 font-bold">
                                            {formatDistanceToNow(new Date(a.created_at))} ago
                                        </td>
                                        <td className="px-8 py-6 text-right">
                                            <button 
                                                onClick={() => router.push(`/dashboard/applications/review/${a.id}`)}
                                                className="px-4 py-2 bg-zinc-900 text-white rounded-xl font-black text-[10px] uppercase tracking-widest italic hover:bg-primary transition-all"
                                            >
                                                Audit Data
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Empty State */}
            {applicants.length === 0 && !loading && (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[40px] p-24 text-center space-y-6">
                     <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-200">
                         <Users className="w-12 h-12" />
                     </div>
                     <div>
                         <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight">Zero Metrics Detected</h3>
                         <p className="text-gray-500 font-bold max-w-sm mx-auto">No candidate protocols have been successfully transmitted for this mission yet.</p>
                     </div>
                </div>
            )}
        </div>
    );
}
