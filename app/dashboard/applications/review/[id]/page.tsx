"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, FileText, CheckCircle2, 
    XCircle, User, Zap, Star, MessageSquare,
    Save, Download, Globe, GraduationCap,
    Send, BrainCircuit, Rocket, Trash2, ArrowRight,
    Mail, Calendar, Briefcase, MousePointer2, Clock
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { useRouter } from "next/navigation";
import ApplicationTimeline from "@/components/applications/ApplicationTimeline";
import ApplicationNotes from "@/components/applications/ApplicationNotes";

export default function ApplicantReviewPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    const [application, setApplication] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [rating, setRating] = useState(0);
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<"audit" | "recon" | "intent" | "history">("audit");

    useEffect(() => {
        const fetchReviewData = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Mark as viewed if first time
            const { data: currentApp } = await supabase.from("job_applications").select("viewed_at").eq("id", id).single();
            if (currentApp && !currentApp.viewed_at) {
                await supabase.from("job_applications").update({ viewed_at: new Date().toISOString() }).eq("id", id);
            }

            const { data, error } = await supabase
                .from("job_applications")
                .select(`
                    *,
                    candidate:profiles!candidate_id(*),
                    job:jobs(*),
                    resume:resumes(*)
                `)
                .eq("id", id)
                .single();

            if (data) {
                setApplication(data);
                setRating(data.recruiter_rating || 0);
            }
            setLoading(false);
        };

        fetchReviewData();
    }, [supabase, id]);

    const handleSaveRating = async (newRating: number) => {
        setRating(newRating);
        await supabase
            .from("job_applications")
            .update({ recruiter_rating: newRating })
            .eq("id", id);
    };

    const handleStatusMove = async (nextStatus: string) => {
        const { data: { user } } = await supabase.auth.getUser();
        
        const { error } = await supabase
            .from("job_applications")
            .update({ status: nextStatus })
            .eq("id", id);
        
        if (!error) {
            setApplication((prev: any) => ({ ...prev, status: nextStatus }));
        }
    };

    const handleToggleShortlist = async () => {
        const newVal = !application.is_shortlisted;
        const { error } = await supabase
            .from("job_applications")
            .update({ is_shortlisted: newVal })
            .eq("id", id);
        
        if (!error) {
            setApplication((prev: any) => ({ ...prev, is_shortlisted: newVal }));
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!application) return <div>Data Audit Failed. Invalid Identifier.</div>;

    const STAGES = [
        { id: "screening", label: "Vetting", icon: <Zap className="w-4 h-4" /> },
        { id: "interview", label: "Interview", icon: <BrainCircuit className="w-4 h-4" /> },
        { id: "offer", label: "Offer", icon: <Rocket className="w-4 h-4" /> },
        { id: "hired", label: "Hire", icon: <CheckCircle2 className="w-4 h-4" /> },
        { id: "rejected", label: "Reject", icon: <XCircle className="w-4 h-4" /> }
    ];

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-24">
            {/* Header */}
            <header className="flex flex-col space-y-8">
                 <Link 
                    href={`/dashboard/jobs/${application.job_id}/applicants`} 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Pipeline Matrix</span>
                </Link>

                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
                    <div className="flex items-center space-x-6">
                        <div className="relative group">
                            <div className="w-24 h-24 bg-gray-50 rounded-[40px] border border-gray-100 flex items-center justify-center font-black text-primary italic overflow-hidden shadow-xl ring-4 ring-white transition-transform group-hover:scale-105">
                                {application.candidate.avatar_url ? (
                                    <img src={application.candidate.avatar_url} className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-4xl">{application.candidate.full_name[0]}</span>
                                )}
                            </div>
                            <button 
                                onClick={handleToggleShortlist}
                                className={`absolute -top-2 -right-2 p-3 rounded-2xl shadow-xl transition-all ${
                                    application.is_shortlisted ? "bg-amber-400 text-white" : "bg-white text-gray-300 border border-gray-100 hover:text-amber-400"
                                }`}
                            >
                                <Star className={`w-5 h-5 ${application.is_shortlisted ? "fill-current" : ""}`} />
                            </button>
                        </div>
                        <div>
                            <div className="flex items-center space-x-3 mb-1">
                                <span className="px-2 py-0.5 bg-primary/10 text-primary text-[8px] font-black uppercase tracking-widest rounded-lg border border-primary/20">Candidate Node</span>
                                {application.viewed_at && (
                                    <span className="text-[8px] font-black text-emerald-500 uppercase tracking-widest flex items-center space-x-1">
                                        <CheckCircle2 className="w-3 h-3" />
                                        <span>Viewed</span>
                                    </span>
                                )}
                            </div>
                            <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none mb-2">
                                {application.candidate.full_name}
                            </h1>
                            <p className="text-lg font-bold text-gray-500 italic uppercase tracking-widest flex items-center space-x-2">
                                <Globe className="w-4 h-4" />
                                <span>{application.job.title} Applicant</span>
                            </p>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {STAGES.map(s => (
                            <button
                                key={s.id}
                                onClick={() => handleStatusMove(s.id)}
                                className={`px-6 py-4 rounded-[24px] flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest transition-all ${
                                    application.status === s.id 
                                    ? s.id === "rejected" ? "bg-red-500 text-white shadow-xl" : "bg-primary text-white shadow-xl" 
                                    : "bg-white border border-gray-100 text-gray-400 hover:bg-gray-50"
                                }`}
                            >
                                {s.icon}
                                <span>{s.label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* Sidebar Metrics (4 columns) */}
                <div className="lg:col-span-4 space-y-8">
                    {/* Neural Match Summary */}
                    <div className="bg-zinc-900 rounded-[48px] p-10 shadow-2xl relative overflow-hidden group">
                        <div className="relative z-10 space-y-6">
                            <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic">Neural Match Core</h4>
                            <div className="flex items-end space-x-2">
                                <h3 className="text-6xl font-black text-white italic tracking-tighter leading-none">{application.match_score || 85}</h3>
                                <span className="text-2xl font-black text-primary italic mb-1">%</span>
                            </div>
                            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                                <motion.div 
                                    initial={{ width: 0 }}
                                    animate={{ width: `${application.match_score || 85}%` }}
                                    transition={{ duration: 1.5, ease: "circOut" }}
                                    className="h-full bg-primary shadow-[0_0_20px_rgba(0,102,255,0.8)]"
                                />
                            </div>
                            
                            <div className="grid grid-cols-2 gap-4 pt-4">
                                <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                                    <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Vibe Sync</p>
                                    <p className="text-sm font-black text-emerald-400 italic">High Alignment</p>
                                </div>
                                <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
                                    <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Radius</p>
                                    <p className="text-sm font-black text-primary italic">In Bounds</p>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-white/10">
                                <div className="flex items-center justify-between mb-4">
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Recruiter Rating</p>
                                    <div className="flex space-x-1">
                                        {[1, 2, 3, 4, 5].map(star => (
                                            <button 
                                                key={star}
                                                onClick={() => handleSaveRating(star)}
                                                className={`transition-all ${rating >= star ? "text-primary scale-110" : "text-white/10 hover:text-white/20"}`}
                                            >
                                                <Star className={`w-4 h-4 ${rating >= star ? "fill-current" : ""}`} />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="absolute right-0 bottom-0 w-64 h-64 bg-primary/20 blur-[100px] rounded-full translate-x-1/2 translate-y-1/2" />
                    </div>

                    {/* Quick Audit Metadata */}
                    <div className="bg-white border border-gray-100 rounded-[48px] p-8 shadow-sm space-y-6">
                        <div className="flex items-center space-x-3 text-primary mb-2">
                             <Briefcase className="w-5 h-5" />
                             <h4 className="text-[10px] font-black uppercase tracking-widest italic underline decoration-2 decoration-primary/20">Mission Metadata</h4>
                        </div>
                        <div className="space-y-4">
                            <MetaItem label="Protocol Initiated" value={formatDistanceToNow(new Date(application.created_at)) + " ago"} />
                            <MetaItem label="Source Discovery" value={application.source || "Direct Link"} />
                            <MetaItem label="Job Department" value={application.job.department || "General"} />
                            <MetaItem label="Resume Status" value={application.resume?.status || "Uploaded"} />
                        </div>
                    </div>

                    {/* Action Controls */}
                    <div className="space-y-4">
                        <button className="w-full py-5 border-2 border-primary/20 bg-primary/5 text-primary rounded-[32px] font-black text-xs uppercase tracking-[0.2em] italic hover:bg-primary hover:text-white transition-all flex items-center justify-center space-x-3 group shadow-xl shadow-primary/5">
                            <Mail className="w-4 h-4 group-hover:scale-110 transition-transform" />
                            <span>Dispatch Comms</span>
                        </button>
                        <button 
                            onClick={() => handleStatusMove('rejected')}
                            className="w-full py-5 border-2 border-red-400/20 bg-red-400/5 text-red-500 rounded-[32px] font-black text-xs uppercase tracking-[0.2em] italic hover:bg-red-500 hover:text-white transition-all flex items-center justify-center space-x-3"
                        >
                            <Trash2 className="w-4 h-4" />
                            <span>Abort Protocol</span>
                        </button>
                    </div>
                </div>

                {/* Main Audit Workspace (8 columns) */}
                <div className="lg:col-span-8 space-y-10">
                    <div className="flex items-center space-x-2 bg-gray-100 p-1.5 rounded-[28px] w-fit">
                        {[
                            { id: "audit", label: "Intelligence", icon: <BrainCircuit className="w-4 h-4" /> },
                            { id: "recon", label: "Recon", icon: <User className="w-4 h-4" /> },
                            { id: "intent", label: "Intent", icon: <MessageSquare className="w-4 h-4" /> },
                            { id: "history", label: "History", icon: <Clock className="w-4 h-4" /> }
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={`px-6 py-3 rounded-[20px] flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest transition-all ${
                                    activeTab === tab.id ? "bg-white text-zinc-900 shadow-sm" : "text-gray-400 hover:text-gray-600"
                                }`}
                            >
                                {tab.icon}
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </div>

                    <AnimatePresence mode="wait">
                        {activeTab === "audit" && (
                            <motion.div
                                key="audit"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-10"
                            >
                                <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm">
                                    <div className="flex items-center space-x-3 mb-10">
                                         <div className="p-3 bg-secondary/10 text-secondary rounded-2xl">
                                             <MessageSquare className="w-5 h-5" />
                                         </div>
                                         <h3 className="text-2xl font-black text-zinc-900 italic uppercase">Internal Intelligence</h3>
                                    </div>
                                    <ApplicationNotes applicationId={id} />
                                </div>
                            </motion.div>
                        )}

                        {activeTab === "recon" && (
                            <motion.div
                                key="recon"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-10"
                            >
                                <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10">
                                     <div className="space-y-4">
                                        <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic ml-2">Identity Narrative</h5>
                                        <p className="text-sm text-gray-600 font-bold italic leading-relaxed bg-gray-50 p-6 rounded-[32px] border border-gray-100">
                                            {application.candidate.bio || "No biography transmitted in this data packet."}
                                        </p>
                                     </div>

                                     <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-6">
                                            <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic ml-2">Screening Vitals</h5>
                                            <div className="space-y-4">
                                                {application.answers ? Object.entries(application.answers).map(([key, val]: any) => (
                                                    <div key={key} className="bg-white border border-gray-100 rounded-3xl p-6 hover:border-primary/20 transition-all">
                                                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mb-3 italic">Question Node: {key.substring(0, 8)}</p>
                                                        <p className="text-sm font-black text-zinc-900 leading-tight">{typeof val === 'string' ? val : JSON.stringify(val)}</p>
                                                    </div>
                                                )) : (
                                                    <p className="text-xs text-gray-400 font-bold italic">No screening protocols required for this mission.</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="space-y-6">
                                            <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic ml-2">Deployed Blueprint</h5>
                                            <div className="bg-zinc-900 rounded-[40px] p-10 relative overflow-hidden group">
                                                 <FileText className="w-16 h-16 text-white/5 mb-6 group-hover:text-primary transition-colors duration-500" />
                                                 <h4 className="text-xl font-black text-white italic tracking-tight mb-2">
                                                     {application.resume?.title || "No Primary Blueprint"}
                                                 </h4>
                                                 <p className="text-[10px] text-gray-500 font-black mb-8 uppercase tracking-[0.2em]">
                                                     {application.resume ? "VERIFIED PDF PACKET" : "DATA PACKET MISSING"}
                                                 </p>
                                                 {application.resume?.file_url ? (
                                                     <Link 
                                                        href={application.resume.file_url} 
                                                        target="_blank"
                                                        className="inline-flex px-8 py-4 bg-white text-zinc-900 rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-primary hover:text-white transition-all shadow-2xl"
                                                     >
                                                        <Download className="w-4 h-4 mr-2" />
                                                        Extract Data
                                                     </Link>
                                                 ) : (
                                                     <div className="inline-flex px-8 py-4 bg-white/5 text-gray-500 rounded-2xl font-black text-[10px] uppercase tracking-widest italic border border-white/10 cursor-not-allowed">
                                                        Blueprint Unavailable
                                                     </div>
                                                 )}
                                                 <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-40 transition-opacity">
                                                     <ArrowRight className="w-12 h-12 text-white -rotate-45" />
                                                 </div>
                                            </div>
                                        </div>
                                     </div>
                                </section>
                            </motion.div>
                        )}

                        {activeTab === "intent" && (
                            <motion.div
                                key="intent"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm"
                            >
                                <div className="flex items-center space-x-4 border-b border-gray-50 pb-8 mb-10">
                                    <div className="p-4 bg-secondary/10 text-secondary rounded-2xl">
                                        <MessageSquare className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-black text-zinc-900 italic uppercase">Intent Transmission</h3>
                                </div>
                                <div className="prose prose-zinc max-w-none font-body text-gray-600 leading-relaxed italic whitespace-pre-wrap text-lg bg-gray-50/50 p-10 rounded-[40px] border border-gray-100">
                                    {application.cover_letter || "No intent packet was included in this transmission."}
                                </div>
                            </motion.div>
                        )}

                        {activeTab === "history" && (
                            <motion.div
                                key="history"
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm"
                            >
                                <div className="flex items-center space-x-4 border-b border-gray-50 pb-8 mb-10">
                                    <div className="p-4 bg-primary/10 text-primary rounded-2xl">
                                        <Clock className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-black text-zinc-900 italic uppercase">Temporal Audit Log</h3>
                                </div>
                                <ApplicationTimeline applicationId={id} />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

function MetaItem({ label, value }: { label: string, value: string }) {
    return (
        <div className="flex items-center justify-between group">
            <span className="text-[9px] font-black text-gray-400 uppercase tracking-widest italic group-hover:text-primary transition-colors">{label}</span>
            <span className="text-xs font-black text-zinc-900 italic tracking-tight">{value}</span>
        </div>
    );
}
