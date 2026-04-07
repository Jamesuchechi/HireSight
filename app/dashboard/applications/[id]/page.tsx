"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, FileText, Clock, CheckCircle2, 
    XCircle, AlertCircle, Share2, Briefcase, 
    MapPin, Globe, DollarSign, BrainCircuit,
    Zap, Trash2
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { useRouter } from "next/navigation";

export default function ApplicationDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    const [application, setApplication] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetail = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Fetch Application & Job
            const { data: appData, error: appError } = await supabase
                .from("job_applications")
                .select(`
                    *,
                    job:jobs(id, title, description, location, remote_type, job_type, salary_min, salary_max, salary_period, currency, department,
                    profiles!company_id(full_name, avatar_url)),
                    resume:resumes(title, file_url)
                `)
                .eq("id", id)
                .single();

            if (appError || !appData) {
                console.error(appError);
                return;
            }

            // Fetch Public History
            const { data: historyData } = await supabase
                .from("application_status_history")
                .select("*")
                .eq("application_id", id)
                .eq("is_public", true)
                .order("created_at", { ascending: false });

            setApplication(appData);
            setHistory(historyData || []);
            setLoading(false);
        };

        fetchDetail();
    }, [supabase, id]);

    const handleWithdraw = async () => {
        if (!confirm("Are you sure you want to withdraw this application? This action is permanent.")) return;

        const { error } = await supabase
            .from("job_applications")
            .delete()
            .eq("id", id);

        if (!error) {
            router.push("/dashboard/applications");
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!application) return <div>Application Not Found</div>;

    const statusConfig: Record<string, { color: string, bg: string, icon: any, label: string }> = {
        applied: { color: "text-blue-500", bg: "bg-blue-50", icon: <Clock className="w-5 h-5" />, label: "Applied" },
        screening: { color: "text-primary", bg: "bg-primary/10", icon: <Zap className="w-5 h-5" />, label: "Initial Screening" },
        interview: { color: "text-secondary", bg: "bg-secondary/10", icon: <BrainCircuit className="w-5 h-5" />, label: "Interviews Active" },
        offer: { color: "text-emerald-500", bg: "bg-emerald-50", icon: <CheckCircle2 className="w-5 h-5" />, label: "Offer Extended" },
        hired: { color: "text-emerald-600", bg: "bg-emerald-100", icon: <CheckCircle2 className="w-5 h-5" />, label: "Mission Accomplished" },
        rejected: { color: "text-red-500", bg: "bg-red-50", icon: <XCircle className="w-5 h-5" />, label: "Mission Aborted" }
    };

    const currentStatus = statusConfig[application.status] || statusConfig.applied;

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20">
            {/* Header */}
            <header className="flex flex-col space-y-8">
                 <Link 
                    href="/dashboard/applications" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Protocol List</span>
                </Link>

                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                            <div className="w-12 h-12 bg-gray-50 rounded-[20px] border border-gray-100 flex items-center justify-center font-black text-primary italic overflow-hidden shadow-sm">
                                {application.job.profiles.avatar_url ? (
                                    <img src={application.job.profiles.avatar_url} className="w-full h-full object-cover" alt="" />
                                ) : (
                                    <span className="text-xl">{application.job.profiles.full_name[0]}</span>
                                )}
                            </div>
                            <div>
                                <h1 className="text-3xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none">
                                    {application.job.title}
                                </h1>
                                <p className="text-lg font-bold text-gray-500 italic mt-1">{application.job.profiles.full_name}</p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className={`px-8 py-5 rounded-[24px] flex items-center space-x-3 shadow-xl ${currentStatus.bg} ${currentStatus.color}`}>
                            {currentStatus.icon}
                            <span className="text-xs font-black uppercase tracking-[0.2em]">{currentStatus.label}</span>
                        </div>
                        <button 
                            onClick={handleWithdraw}
                            className="p-5 bg-white border border-gray-100 rounded-[24px] text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all shadow-sm group"
                        >
                            <Trash2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        </button>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                {/* Protocol Details (Main) */}
                <div className="lg:col-span-2 space-y-12">
                    {/* Status Timeline */}
                    <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10">
                        <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Protocol Evolution</h3>
                        <div className="relative space-y-10 pl-8">
                             {/* Vertical Line */}
                             <div className="absolute left-[15px] top-4 bottom-4 w-1 bg-gray-100 rounded-full" />
                             
                             {history.map((h, i) => (
                                 <div key={h.id} className="relative">
                                     <div className={`absolute -left-[23px] w-[14px] h-[14px] rounded-full border-4 border-white shadow-md z-10 ${
                                         i === 0 ? "bg-primary scale-150" : "bg-gray-300"
                                     }`} />
                                     <div className="space-y-1">
                                         <div className="flex items-center space-x-3">
                                            <span className="text-xs font-black text-zinc-900 uppercase tracking-widest">{h.new_status}</span>
                                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{formatDistanceToNow(new Date(h.created_at))} ago</span>
                                         </div>
                                         <p className="text-sm text-gray-500 font-bold italic">{h.reason || "Automatic status transition."}</p>
                                     </div>
                                 </div>
                             ))}
                        </div>
                    </section>

                    {/* Cover Letter Matrix */}
                    {application.cover_letter && (
                        <section className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm space-y-8">
                            <div className="flex items-center space-x-3 border-b border-gray-50 pb-6">
                                <FileText className="w-6 h-6 text-primary" />
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Cover Letter Matrix</h3>
                            </div>
                            <div className="prose prose-zinc max-w-none font-body text-gray-600 leading-relaxed italic whitespace-pre-wrap">
                                {application.cover_letter}
                            </div>
                        </section>
                    )}

                    {/* Job Reference */}
                    <Link href={`/jobs/${application.job.id}`} className="block bg-zinc-900 rounded-[48px] p-12 shadow-2xl relative overflow-hidden group">
                        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
                             <div className="space-y-4">
                                <h4 className="text-sm font-black text-primary uppercase tracking-[0.3em]">Reference Mission</h4>
                                <h3 className="text-3xl font-black text-white italic tracking-tight">{application.job.title}</h3>
                                <div className="flex flex-wrap gap-4 items-center">
                                    <div className="flex items-center space-x-2 text-gray-400 text-xs font-bold italic">
                                        <MapPin className="w-4 h-4" />
                                        <span>{application.job.location}</span>
                                    </div>
                                    <div className="flex items-center space-x-2 text-gray-400 text-xs font-bold italic">
                                        <DollarSign className="w-4 h-4" />
                                        <span>${(application.job.salary_min / 1000).toFixed(0)}k - ${(application.job.salary_max / 1000).toFixed(0)}k</span>
                                    </div>
                                </div>
                             </div>
                             <div className="px-8 py-4 bg-white/10 rounded-2xl text-white font-black text-[10px] uppercase tracking-widest border border-white/10 group-hover:bg-primary group-hover:border-primary transition-all">
                                View Blueprint
                             </div>
                        </div>
                        <div className="absolute right-0 top-0 w-64 h-64 bg-primary/10 blur-[100px] rounded-full" />
                    </Link>
                </div>

                {/* Sidebar (Right) */}
                <div className="space-y-8">
                     {/* Identity Matrix Used */}
                     <div className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm space-y-6">
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Identity Matrix Deployed</h4>
                        <div className="flex items-center space-x-4">
                            <div className="p-4 bg-gray-100 rounded-[20px] text-gray-400">
                                <FileText className="w-6 h-6" />
                            </div>
                            <div className="overflow-hidden">
                                <h5 className="text-sm font-black text-zinc-900 italic tracking-tight truncate">{application.resume?.title || "Master Resume"}</h5>
                                <Link 
                                    href={application.resume?.file_url || "#"} 
                                    target="_blank"
                                    className="text-[10px] font-black text-primary uppercase tracking-[0.2em] hover:underline"
                                >
                                    Review Blueprint
                                </Link>
                            </div>
                        </div>
                     </div>

                     {/* Company Feedback Matrix */}
                     {application.feedback && (
                        <div className="bg-emerald-50 border border-emerald-100 rounded-[40px] p-10 space-y-4">
                            <div className="flex items-center space-x-2 text-emerald-600">
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest italic">Company Message</span>
                            </div>
                            <p className="text-sm text-emerald-900 font-bold italic leading-relaxed">
                                "{application.feedback}"
                            </p>
                        </div>
                     )}

                     {/* Intelligence Stats */}
                     <div className="bg-zinc-900 rounded-[40px] p-8 shadow-xl space-y-6">
                         <div className="space-y-1">
                            <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none">Neural Match Score</p>
                            <h4 className="text-4xl font-black text-white italic tracking-tighter">{application.match_score || "85"}%</h4>
                         </div>
                         <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                             <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${application.match_score || 85}%` }}
                                transition={{ duration: 1, delay: 0.5 }}
                                className="h-full bg-primary shadow-[0_0_15px_rgba(0,102,255,0.8)]"
                             />
                         </div>
                         <p className="text-[10px] text-gray-400 font-bold leading-relaxed italic uppercase tracking-[0.1em]">Your profile matrix highly aligns with the core constraints of this mission.</p>
                     </div>
                </div>
            </div>
        </div>
    );
}
