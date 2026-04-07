"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Calendar, Clock, Video, Code, Users, 
    ChevronRight, BrainCircuit, Star, 
    MoreVertical, ArrowRight, Play, CheckCircle2,
    Search, Filter, Plus
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { format, isAfter, isBefore, addMinutes, isWithinInterval } from "date-fns";
import Link from "next/link";
import { useRouter } from "next/navigation";
import PracticeSetup from "@/components/interviews/PracticeSetup";
import RescheduleModal from "@/components/interviews/RescheduleModal";
import { notify } from "@/lib/notifications/notify";

export default function InterviewsHubPage() {
    const supabase = createClient();
    const router = useRouter();
    const [interviews, setInterviews] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<"upcoming" | "past" | "practice">("upcoming");
    const [userRole, setUserRole] = useState<"candidate" | "recruiter" | null>(null);
    const [isPracticeSetupOpen, setIsPracticeSetupOpen] = useState(false);

    useEffect(() => {
    const fetchInterviews = async () => {
        setLoading(true);
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        // Get User Role
        const { data: profile } = await supabase.from('profiles').select('role').eq('id', user.id).single();
        setUserRole(profile?.role);

        // Fetch Interviews where user is a participant
        const { data, error } = await supabase
            .from('interviews')
            .select(`
                *,
                job_application:job_applications(
                    candidate:profiles!candidate_id(id, full_name, avatar_url),
                    job:jobs(id, title, company_id, profiles!company_id(id, full_name, avatar_url))
                ),
                participants:interview_participants(
                    role,
                    profile:profiles(id, full_name, avatar_url)
                )
            `)
            .order('scheduled_at', { ascending: true });

        if (data) setInterviews(data);
        setLoading(false);
    };

    useEffect(() => {
        fetchInterviews();
    }, [supabase]);

    const filteredInterviews = interviews.filter(i => {
        const date = new Date(i.scheduled_at);
        if (activeTab === "upcoming") return isAfter(addMinutes(date, i.duration_minutes), new Date());
        if (activeTab === "past") return isBefore(addMinutes(date, i.duration_minutes), new Date());
        return false;
    });

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20">
            {/* ... header and tabs code ... */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
                >
                    {filteredInterviews.length > 0 ? (
                        filteredInterviews.map((interview) => (
                            <InterviewCard 
                                key={interview.id} 
                                interview={interview} 
                                role={userRole}
                                onRefresh={fetchInterviews} 
                            />
                        ))
                    ) : (
                        <EmptyState 
                            tab={activeTab} 
                            role={userRole} 
                            onStartPractice={() => setIsPracticeSetupOpen(true)}
                        />
                    )}
                </motion.div>
            </AnimatePresence>

            <PracticeSetup 
                isOpen={isPracticeSetupOpen}
                onClose={() => setIsPracticeSetupOpen(false)}
                onComplete={(id) => router.push(`/dashboard/interviews/practice/${id}`)}
            />
        </div>
    );
}

function InterviewCard({ interview, role, onRefresh }: { interview: any, role: any, onRefresh: () => void }) {
    const supabase = createClient();
    const [isRescheduling, setIsRescheduling] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);

    const isLive = isWithinInterval(new Date(), {
        start: new Date(interview.scheduled_at),
        end: addMinutes(new Date(interview.scheduled_at), interview.duration_minutes)
    });

    const isUpcoming = isAfter(new Date(interview.scheduled_at), new Date());

    const opponent = role === "recruiter" 
        ? interview.job_application.candidate 
        : interview.job_application.job.profiles;

    const handleAction = async (action: 'accepted' | 'declined' | 'cancelled' | 'no_show' | 'confirm_reschedule' | 'reject_reschedule') => {
        setIsProcessing(true);
        try {
            let updateData: any = {};
            
            if (action === 'accepted' || action === 'declined') {
                updateData.candidate_response = action;
            } else if (action === 'cancelled' || action === 'no_show') {
                updateData.status = action;
            } else if (action === 'confirm_reschedule') {
                const latestProposal = interview.proposed_times[interview.proposed_times.length - 1];
                updateData.scheduled_at = latestProposal.date;
                updateData.candidate_response = 'accepted';
                updateData.status = 'rescheduled';
            } else if (action === 'reject_reschedule') {
                updateData.candidate_response = 'pending';
            }

            const { error } = await supabase
                .from('interviews')
                .update(updateData)
                .eq('id', interview.id);

            if (error) throw error;

            // Notify Partner
            const partner = interview.participants.find((p: any) => p.profile_id !== (await supabase.auth.getUser()).data.user?.id);
            if (partner) {
                await notify(partner.profile_id, {
                    title: `Protocol Update: ${action.toUpperCase()}`,
                    message: `The mission ${interview.job_application.job.title} has been updated.`,
                    type: "interview_updated"
                });
            }

            onRefresh();
        } catch (error) {
            console.error("Action Failed:", error);
        } finally {
            setIsProcessing(false);
        }
    };

    const latestProposal = interview.candidate_response === 'proposed_reschedule' && interview.proposed_times?.length > 0 
        ? interview.proposed_times[interview.proposed_times.length - 1] 
        : null;

    return (
        <div className={`bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm hover:shadow-2xl transition-all duration-500 group relative overflow-hidden flex flex-col h-full ${isLive ? 'ring-2 ring-primary ring-offset-4 ring-offset-gray-50' : ''}`}>
            {/* Status Batch */}
            <div className="flex items-center justify-between mb-8">
                <div className={`px-4 py-2 rounded-full flex items-center space-x-2 ${
                    isLive ? 'bg-primary text-white' : 
                    latestProposal ? 'bg-indigo-50 text-indigo-600' :
                    isUpcoming ? 'bg-amber-50 text-amber-600' : 'bg-gray-100 text-gray-500'
                }`}>
                    {isLive ? (
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
                        </span>
                    ) : (
                        <Clock className="w-3 h-3" />
                    )}
                    <span className="text-[10px] font-black uppercase tracking-widest italic leading-none">
                        {isLive ? "Active Session" : latestProposal ? "Reschedule Proposed" : interview.status}
                    </span>
                </div>
                <div className="text-gray-300 group-hover:text-primary transition-colors">
                    {interview.type === "video" ? <Video className="w-5 h-5" /> : <Code className="w-5 h-5" />}
                </div>
            </div>

            {/* Context */}
            <div className="space-y-6 flex-grow">
                <div>
                     <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic mb-1">Mission Protocol</p>
                     <h3 className="text-2xl font-black text-zinc-900 italic tracking-tighter leading-tight group-hover:text-primary transition-colors">
                        {interview.job_application.job.title}
                     </h3>
                </div>

                <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden shrink-0">
                        {opponent.avatar_url ? (
                            <img src={opponent.avatar_url} className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center font-black text-primary italic">
                                {opponent.full_name?.[0]}
                            </div>
                        )}
                    </div>
                    <div>
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic leading-none">Primary Asset</p>
                        <p className="text-sm font-black text-zinc-900 italic">{opponent.full_name}</p>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50/50 rounded-2xl border border-gray-100">
                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mb-1 italic">T-Minus</p>
                        <p className="text-xs font-black text-zinc-900">{format(new Date(interview.scheduled_at), "MMM do, HH:mm")}</p>
                    </div>
                    <div className="p-4 bg-gray-50/50 rounded-2xl border border-gray-100">
                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mb-1 italic">Duration</p>
                        <p className="text-xs font-black text-zinc-900">{interview.duration_minutes}m Session</p>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="pt-8 mt-auto space-y-4">
                {role === "candidate" && interview.candidate_response === "pending" && (
                    <div className="grid grid-cols-2 gap-3 mb-4">
                        <button 
                            onClick={() => handleAction('accepted')}
                            disabled={isProcessing}
                            className="py-3 bg-emerald-500 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-emerald-600 transition-all flex items-center justify-center space-x-2"
                        >
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Confirm</span>
                        </button>
                        <button 
                            onClick={() => setIsRescheduling(true)}
                            disabled={isProcessing}
                            className="py-3 bg-amber-500 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-amber-600 transition-all flex items-center justify-center space-x-2"
                        >
                            <Clock className="w-3 h-3" />
                            <span>Reschedule</span>
                        </button>
                    </div>
                )}

                {role === "recruiter" && latestProposal && (
                    <div className="bg-indigo-50/50 p-6 rounded-[32px] border border-indigo-100 mb-4 space-y-4">
                        <p className="text-[9px] font-black text-indigo-500 uppercase tracking-widest italic leading-none">Proposal Detected</p>
                        <p className="text-xs font-bold text-zinc-900 italic">
                            New Tactical Window: <span className="text-indigo-600">{format(new Date(latestProposal.date), "MMM do, HH:mm")}</span>
                        </p>
                        <div className="grid grid-cols-2 gap-2">
                            <button 
                                onClick={() => handleAction('confirm_reschedule')}
                                className="py-2.5 bg-indigo-600 text-white rounded-xl font-black text-[8px] uppercase tracking-widest italic hover:bg-indigo-700 transition-all"
                            >
                                Confirm Sync
                            </button>
                            <button 
                                onClick={() => handleAction('reject_reschedule')}
                                className="py-2.5 bg-white text-indigo-600 border border-indigo-200 rounded-xl font-black text-[8px] uppercase tracking-widest italic hover:bg-indigo-50 transition-all"
                            >
                                Decline
                            </button>
                        </div>
                    </div>
                )}

                <div className="flex items-center space-x-2">
                    <Link 
                        href={`/dashboard/interviews/${interview.id}`}
                        className={`flex-grow py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] italic flex items-center justify-center space-x-2 transition-all ${
                            isLive 
                            ? 'bg-primary text-white shadow-xl shadow-primary/20 hover:scale-[1.02]' 
                            : 'bg-zinc-900 text-white hover:bg-primary'
                        }`}
                    >
                        <span>{isLive ? "Engage Protocol" : "Review Intelligence"}</span>
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                    
                    {role === "recruiter" && (
                         <div className="relative group/menu">
                            <button className="p-4 bg-gray-50 text-gray-400 rounded-2xl hover:text-red-500 transition-colors">
                                <MoreVertical className="w-4 h-4" />
                            </button>
                            <div className="absolute bottom-full right-0 mb-2 w-48 bg-white rounded-3xl shadow-2xl border border-gray-100 py-3 scale-0 group-hover/menu:scale-100 transition-all origin-bottom-right z-50">
                                <button 
                                    onClick={() => handleAction('cancelled')}
                                    className="w-full text-left px-6 py-2.5 text-[10px] font-black uppercase tracking-widest italic text-red-500 hover:bg-red-50"
                                >
                                    Abort Mission
                                </button>
                                <button 
                                    onClick={() => handleAction('no_show')}
                                    className="w-full text-left px-6 py-2.5 text-[10px] font-black uppercase tracking-widest italic text-gray-500 hover:bg-gray-50"
                                >
                                    Report MIA
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <RescheduleModal 
                isOpen={isRescheduling}
                onClose={() => setIsRescheduling(false)}
                interview={interview}
                onComplete={onRefresh}
            />

            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl rounded-full -translate-y-1/2 translate-x-1/2 group-hover:bg-primary/10 transition-colors" />
        </div>
    );
}

function EmptyState({ tab, role, onStartPractice }: { tab: string, role: any, onStartPractice?: () => void }) {
    return (
        <div className="col-span-1 md:col-span-2 lg:col-span-3 bg-white border-2 border-dashed border-gray-100 rounded-[48px] p-24 text-center space-y-8 shadow-sm">
            <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-200">
                {tab === "practice" ? <Play className="w-12 h-12" /> : <Calendar className="w-12 h-12" />}
            </div>
            <div className="space-y-2">
                <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight uppercase">Protocol Silence</h3>
                <p className="text-gray-500 font-bold max-w-sm mx-auto italic">
                    No active mission protocols detected in the current matrix.
                </p>
            </div>
            {role === "candidate" && tab === "practice" && (
                <button 
                    onClick={onStartPractice}
                    className="px-10 py-5 bg-primary text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic hover:scale-[1.05] transition-all shadow-xl shadow-primary/20"
                >
                    Initialize Training Mission
                </button>
            )}
        </div>
    );
}
