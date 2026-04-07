"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, FileText, CheckCircle2, 
    XCircle, User, Zap, Star, MessageSquare,
    Save, Download, Globe, GraduationCap,
    Send, BrainCircuit, Rocket, Trash2, ArrowRight,
    Mail
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { useRouter } from "next/navigation";

export default function ApplicantReviewPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    const [application, setApplication] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [notes, setNotes] = useState("");
    const [rating, setRating] = useState(0);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        const fetchReviewData = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

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
                setNotes(data.notes || "");
                setRating(data.rating || 0);
            }
            setLoading(false);
        };

        fetchReviewData();
    }, [supabase, id]);

    const handleSaveReview = async () => {
        setIsSaving(true);
        const { error } = await supabase
            .from("job_applications")
            .update({ notes, rating })
            .eq("id", id);
        
        if (!error) {
            alert("Review saved successfully.");
        }
        setIsSaving(false);
    };

    const handleStatusMove = async (nextStatus: string) => {
        const { error } = await supabase
            .from("job_applications")
            .update({ status: nextStatus })
            .eq("id", id);
        
        if (!error) {
            // Log history
            await supabase.from("application_status_history").insert({
               application_id: id,
               old_status: application.status,
               new_status: nextStatus,
               changed_by: (await supabase.auth.getUser()).data.user?.id,
               reason: `Recruiter moved candidate to ${nextStatus}.`
            });
            setApplication((prev: any) => ({ ...prev, status: nextStatus }));
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
                    <div className="space-y-4">
                        <div className="flex items-center space-x-6">
                            <div className="w-20 h-20 bg-gray-50 rounded-[40px] border border-gray-100 flex items-center justify-center font-black text-primary italic overflow-hidden shadow-xl ring-4 ring-white">
                                {application.candidate.avatar_url ? (
                                    <img src={application.candidate.avatar_url} className="w-full h-full object-cover" />
                                ) : (
                                    <span className="text-3xl">{application.candidate.full_name[0]}</span>
                                )}
                            </div>
                            <div>
                                <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none">
                                    {application.candidate.full_name}
                                </h1>
                                <p className="text-lg font-bold text-gray-500 italic mt-1 uppercase tracking-widest flex items-center space-x-2">
                                    <Globe className="w-4 h-4" />
                                    <span>{application.job.title} Applicant</span>
                                </p>
                            </div>
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

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                {/* Main Review Section (2/3) */}
                <div className="lg:col-span-2 space-y-12">
                     {/* Intelligence Breakdown */}
                     <div className="bg-zinc-900 rounded-[56px] p-12 shadow-2xl relative overflow-hidden group">
                        <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-12 text-center md:text-left">
                            <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic mb-6">Neural Match Core</h4>
                                <div className="flex items-end space-x-2 justify-center md:justify-start">
                                    <h3 className="text-7xl font-black text-white italic tracking-tighter leading-none">{application.match_score || 85}</h3>
                                    <span className="text-2xl font-black text-primary italic mb-2">%</span>
                                </div>
                                <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                                     <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${application.match_score || 85}%` }}
                                        transition={{ duration: 1.5, ease: "circOut" }}
                                        className="h-full bg-primary shadow-[0_0_15px_rgba(0,102,255,0.8)]"
                                     />
                                </div>
                            </div>

                            <div className="md:col-span-2 space-y-6">
                                <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] italic">Constraint Alignment</h4>
                                <div className="grid grid-cols-2 gap-6">
                                    {[
                                        { label: "Skill Variance", val: "92%", color: "text-emerald-500" },
                                        { label: "Exp Logic", val: "High", color: "text-primary" },
                                        { label: "Culture Bias", val: "8.5/10", color: "text-secondary" },
                                        { label: "Radius Sync", val: "In Range", color: "text-zinc-400" }
                                    ].map(stat => (
                                        <div key={stat.label} className="bg-white/5 border border-white/10 rounded-2xl p-4">
                                            <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">{stat.label}</p>
                                            <p className={`text-xl font-black italic ${stat.color}`}>{stat.val}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <div className="absolute right-0 bottom-0 w-80 h-80 bg-primary/20 blur-[120px] rounded-full translate-x-1/2 translate-y-1/2" />
                     </div>

                     {/* Candidate Profile Preview */}
                     <section className="bg-white border border-gray-100 rounded-[56px] p-12 shadow-sm space-y-8">
                        <div className="flex items-center justify-between border-b border-gray-50 pb-8">
                             <div className="flex items-center space-x-4">
                                 <div className="p-4 bg-gray-50 rounded-2xl text-primary">
                                     <User className="w-6 h-6" />
                                 </div>
                                 <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Candidate Profile Matrix</h3>
                             </div>
                             <Link href="#" className="text-[10px] font-black text-primary uppercase tracking-widest hover:underline flex items-center space-x-2">
                                <span>Full Recon Mission</span>
                                <ArrowRight className="w-3 h-3" />
                             </Link>
                        </div>
                        <div className="space-y-6">
                             <div className="space-y-2">
                                <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Identity Narrative</h5>
                                <p className="text-sm text-gray-600 font-bold italic leading-relaxed">
                                    {application.candidate.bio || "No biography transmitted in this data packet."}
                                </p>
                             </div>
                             
                             <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6">
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Screening Responses</h5>
                                    {application.answers ? Object.entries(application.answers).map(([key, val]: any) => (
                                        <div key={key} className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
                                            <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mb-2 italic">Question Index: {key.substring(0, 8)}</p>
                                            <p className="text-sm font-bold text-zinc-900">{typeof val === 'string' ? val : JSON.stringify(val)}</p>
                                        </div>
                                    )) : (
                                        <p className="text-xs text-gray-400 font-bold italic">No screening protocols required for this mission.</p>
                                    )}
                                </div>
                                <div className="space-y-6">
                                     <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Deployed Blueprint</h5>
                                     <div className="bg-zinc-900 rounded-3xl p-8 relative overflow-hidden group">
                                         <FileText className="w-12 h-12 text-white/10 mb-4 group-hover:text-primary transition-colors" />
                                         <h4 className="text-lg font-black text-white italic tracking-tight">{application.resume.title}</h4>
                                         <p className="text-[10px] text-gray-500 font-bold mb-6">DEPLOYED DATA PACKET</p>
                                         <Link 
                                            href={application.resume.file_url} 
                                            target="_blank"
                                            className="inline-flex px-6 py-3 bg-white text-zinc-900 rounded-xl font-black text-[10px] uppercase tracking-widest italic hover:bg-primary hover:text-white transition-all shadow-lg"
                                         >
                                            <Download className="w-4 h-4 mr-2" />
                                            Extract PDF
                                         </Link>
                                     </div>
                                </div>
                             </div>
                        </div>
                     </section>

                     {/* Cover Letter Matrix */}
                     {application.cover_letter && (
                        <section className="bg-white border border-gray-100 rounded-[56px] p-12 shadow-sm space-y-8">
                             <div className="flex items-center space-x-4 border-b border-gray-50 pb-8">
                                <div className="p-4 bg-secondary/10 text-secondary rounded-2xl">
                                    <MessageSquare className="w-6 h-6" />
                                </div>
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Intent Transmission</h3>
                            </div>
                            <div className="prose prose-zinc max-w-none font-body text-gray-600 leading-relaxed italic whitespace-pre-wrap">
                                {application.cover_letter}
                            </div>
                        </section>
                     )}
                </div>

                {/* Sidebar Audit Grid (1/3) */}
                <div className="space-y-8">
                     {/* Internal Audit Notes */}
                     <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                        <div className="flex items-center justify-between">
                            <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Internal Audit</h4>
                            <div className="flex space-x-1">
                                {[1, 2, 3, 4, 5].map(star => (
                                    <button 
                                        key={star}
                                        onClick={() => setRating(star)}
                                        className={`transition-all ${rating >= star ? "text-primary scale-110" : "text-gray-200"}`}
                                    >
                                        <Star className="w-5 h-5 fill-current" />
                                    </button>
                                ))}
                            </div>
                        </div>

                        <textarea 
                            rows={8}
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                            className="w-full bg-gray-50 border border-gray-100 rounded-[32px] p-8 text-sm font-bold italic focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all outline-none resize-none"
                            placeholder="Add internal audit notes..."
                        />

                        <button 
                            onClick={handleSaveReview}
                            disabled={isSaving}
                            className="w-full py-5 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center space-x-3"
                        >
                            {isSaving ? (
                                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                            ) : (
                                <>
                                    <Save className="w-4 h-4" />
                                    <span>Commit Audit</span>
                                </>
                            )}
                        </button>
                     </div>

                     {/* Action Controls */}
                     <div className="space-y-4">
                         <button className="w-full py-5 border-2 border-primary/20 bg-primary/5 text-primary rounded-[32px] font-black text-xs uppercase tracking-[0.2em] italic hover:bg-primary hover:text-white transition-all flex items-center justify-center space-x-3">
                            <Mail className="w-4 h-4" />
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

                     {/* Metadata */}
                     <div className="px-8 space-y-4">
                        <div className="flex items-center justify-between text-[8px] font-black text-gray-400 uppercase tracking-widest border-t border-gray-100 pt-6">
                            <span>Protocol Initiated</span>
                            <span>{new Date(application.created_at).toLocaleDateString()}</span>
                        </div>
                        <div className="flex items-center justify-between text-[8px] font-black text-gray-400 uppercase tracking-widest">
                            <span>Neural Scan ID</span>
                            <span className="truncate w-32 text-right">{application.id.substring(0, 16)}...</span>
                        </div>
                     </div>
                </div>
            </div>
        </div>
    );
}
