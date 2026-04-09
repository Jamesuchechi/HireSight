"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    BrainCircuit, ShieldCheck, Zap, 
    MessageSquare, Settings, User, 
    CheckCircle2, AlertCircle, Loader2,
    X, Menu, ChevronRight, Save, LayoutGrid, Terminal
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import VideoRoom from "@/components/interviews/VideoRoom";
import SharedEditor from "@/components/interviews/SharedEditor";
import WarmupRoom from "@/components/interviews/WarmupRoom";
import ConsentModal from "@/components/interviews/ConsentModal";
import { WhisperFeed, TacticalWhisperInput } from "@/components/interviews/TacticalWhisper";

export default function LiveInterviewRoomPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    
    const [interview, setInterview] = useState<any>(null);
    const [role, setRole] = useState<string | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activePanel, setActivePanel] = useState<"video" | "editor" | "split">("split");
    const [notes, setNotes] = useState("");
    const [isSavingNotes, setIsSavingNotes] = useState(false);
    const [hasConsented, setHasConsented] = useState(false);
    const [isWarmup, setIsWarmup] = useState(true);
    const [whispers, setWhispers] = useState<any[]>([]);

    useEffect(() => {
        const initializeRoom = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            // 1. Fetch Interview Data
            const { data: intData, error: intError } = await supabase
                .from("interviews")
                .select(`
                    *,
                    job_application:job_applications(
                        candidate:profiles!candidate_id(id, full_name, avatar_url),
                        job:jobs(id, title, company_id)
                    )
                `)
                .eq("id", id)
                .single();

            if (intError || !intData) {
                setError("Protocol Access Failed. Invalid Session Identifier.");
                setLoading(false);
                return;
            }
            setInterview(intData);

            // 2. Verify Role & Get Token
            // The Supabase client automatically attaches the auth session header —
            // no need to manually pass Authorization or apikey headers.
            try {
                const response = await supabase.functions.invoke('interviews-token', {
                    body: { interviewId: id },
                });

                if (response.error) {
                    console.error("Function Error:", response.error);
                    throw new Error(response.error.message || "Unauthorized access to protocol.");
                }

                setToken(response.data.token);
                
                // Get local participant role
                const { data: participant } = await supabase
                    .from("interview_participants")
                    .select("role")
                    .eq("interview_id", id)
                    .eq("profile_id", user.id)
                    .single();
                
                setRole(participant?.role || 'observer');

                // 3. Fetch Existing Notes
                const { data: feedback } = await supabase
                    .from("interview_feedback")
                    .select("comments")
                    .eq("interview_id", id)
                    .eq("interviewer_id", user.id)
                    .single();
                
                if (feedback) setNotes(feedback.comments || "");

            } catch (err: any) {
                setError(err.message || "Failed to establish secure link.");
            } finally {
                setLoading(false);
            }
        };

        initializeRoom();
    }, [id, supabase, router]);

    const handleEndInterview = async () => {
        if (!window.confirm("Abort mission? This will finalize the protocol and trigger AI evaluation.")) return;
        setIsSavingNotes(true);
        
        const { error } = await supabase
            .from("interviews")
            .update({ status: "completed" })
            .eq("id", id);
        
        if (!error) {
            // The Supabase client handles auth headers automatically here too.
            await supabase.functions.invoke('interviews-evaluator', {
                body: { interviewId: id },
            });
            router.push(`/dashboard/interviews`);
        }
        setIsSavingNotes(false);
    };

    const saveNotes = async (val: string) => {
        setNotes(val);
        setIsSavingNotes(true);
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        await supabase
            .from("interview_feedback")
            .upsert({
                interview_id: id,
                interviewer_id: user.id,
                comments: val,
                updated_at: new Date().toISOString()
            }, { onConflict: 'interview_id,interviewer_id' });
        
        setTimeout(() => setIsSavingNotes(false), 1000);
    };

    const handleWhisper = (payload: any) => {
        if (payload.type === 'whisper') {
            const newWhisper = {
                id: Math.random().toString(36).substr(2, 9),
                from: payload.from || 'Observer',
                text: payload.text,
                timestamp: new Date()
            };
            setWhispers(prev => [...prev.slice(-4), newWhisper]);
            
            setTimeout(() => {
                setWhispers(prev => prev.filter(w => w.id !== newWhisper.id));
            }, 10000);
        }
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black space-y-8">
            <div className="relative">
                <div className="w-24 h-24 border-4 border-primary/20 rounded-full animate-pulse" />
                <div className="absolute inset-0 w-24 h-24 border-t-4 border-primary rounded-full animate-spin" />
            </div>
            <div className="text-center space-y-2">
                <h3 className="text-2xl font-black text-white italic tracking-tighter uppercase">Initializing Command Link</h3>
                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic animate-pulse">Establishing Peer-to-Peer Encryption...</p>
            </div>
        </div>
    );

    if (error) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black p-6">
            <div className="p-10 bg-red-500/10 border border-red-500/20 rounded-[48px] max-w-md text-center space-y-8">
                <AlertCircle className="w-16 h-16 text-red-500 mx-auto" />
                <div className="space-y-4">
                    <h2 className="text-3xl font-black text-white italic tracking-tighter uppercase">Mission Failed</h2>
                    <p className="text-gray-400 font-bold italic leading-relaxed">{error}</p>
                </div>
                <button 
                    onClick={() => router.push("/dashboard/interviews")}
                    className="w-full py-5 bg-white text-black rounded-[24px] font-black text-xs uppercase tracking-widest italic hover:bg-primary hover:text-white transition-all"
                >
                    Return to Operations
                </button>
            </div>
        </div>
    );

    return (
        <div className="bg-[#0c0c0c] text-white h-screen flex flex-col overflow-hidden relative">
            {/* Mission Pre-flight */}
            <AnimatePresence>
                {isWarmup && (
                    <motion.div
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0, scale: 1.1 }}
                        transition={{ duration: 0.8, ease: "circIn" }}
                        className="fixed inset-0 z-[100]"
                    >
                        <WarmupRoom 
                            onReady={() => setIsWarmup(false)} 
                            candidateName={interview?.job_application?.candidate?.full_name || "Agent"} 
                            interviewType={interview?.type || "Mission"} 
                        />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Privacy Gate */}
            {!hasConsented && !isWarmup && (
                <ConsentModal 
                    isOpen={!hasConsented} 
                    onAccept={() => setHasConsented(true)}
                    onDecline={() => router.push('/dashboard/interviews')}
                />
            )}

            {/* Mission Critical Header */}
            <header className="h-20 bg-black/60 backdrop-blur-3xl border-b border-white/5 flex items-center justify-between px-10 shrink-0 z-50">
                <div className="flex items-center space-x-8">
                    <button 
                        onClick={() => router.push('/dashboard/interviews')}
                        className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5 group"
                    >
                        <ChevronRight className="w-5 h-5 text-gray-400 rotate-180 group-hover:-translate-x-1 transition-transform" />
                    </button>
                    <div className="h-8 w-px bg-white/10" />
                    <div>
                         <div className="flex items-center space-x-3 mb-1">
                             <div className="p-1 bg-primary/20 rounded-md">
                                 <BrainCircuit className="w-3 h-3 text-primary" />
                             </div>
                             <span className="text-[8px] font-black text-primary uppercase tracking-[0.4em] italic">Intelligence Protocol</span>
                         </div>
                         <h2 className="text-lg font-black italic tracking-tighter text-white uppercase leading-none">
                            {interview.job_application.job.title}
                         </h2>
                    </div>
                </div>

                {/* View Switchers */}
                <div className="flex items-center bg-white/5 p-1 rounded-2xl border border-white/5">
                    <ViewButton active={activePanel === 'video'} onClick={() => setActivePanel('video')} icon={<MessageSquare className="w-4 h-4" />} label="Visual" />
                    <ViewButton active={activePanel === 'editor'} onClick={() => setActivePanel('editor')} icon={<Terminal className="w-4 h-4" />} label="Terminal" />
                    <ViewButton active={activePanel === 'split'} onClick={() => setActivePanel('split')} icon={<LayoutGrid className="w-4 h-4" />} label="Dual-Sync" />
                </div>

                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-4 bg-white/5 px-6 py-3 rounded-2xl border border-white/5">
                        <div className="relative">
                            <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(16,185,129,0.8)]" />
                        </div>
                        <span className="text-[10px] font-black text-white uppercase tracking-widest italic">{role} Command</span>
                    </div>

                    <button 
                        onClick={handleEndInterview}
                        className="px-8 py-3.5 bg-red-500 text-white rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] italic hover:scale-105 transition-all shadow-2xl shadow-red-500/20"
                    >
                        Abort Mission
                    </button>
                </div>
            </header>

            {/* Tactical Workspace */}
            <main className="flex-grow relative overflow-hidden flex">
                <AnimatePresence mode="wait">
                    {/* Video Area */}
                    {(activePanel === 'split' || activePanel === 'video') && (
                        <motion.div 
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: activePanel === 'split' ? "40%" : "100%", opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 100, damping: 20 }}
                            className="h-full border-r border-white/5 p-8 overflow-y-auto scrollbar-hide flex flex-col space-y-6"
                        >
                            <div className="h-[400px] shrink-0">
                                {token && (
                                    <VideoRoom 
                                        token={token} 
                                        roomName={`interview-${id}`} 
                                        onDisconnected={() => router.push('/dashboard/interviews')}
                                        onMessage={handleWhisper}
                                    />
                                )}
                            </div>

                            {/* Recruiter Matrix Panel */}
                            {role === 'interviewer' && (
                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="flex-grow bg-white/5 rounded-[40px] p-8 border border-white/5 space-y-6"
                                >
                                    <div className="flex items-center justify-between pb-6 border-b border-white/5">
                                        <div className="flex items-center space-x-3 text-primary">
                                             <Zap className="w-5 h-5 fill-current" />
                                             <h4 className="text-[10px] font-black uppercase tracking-widest italic">Recruiter Intent Matrix</h4>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                             <span className="text-[8px] font-black text-gray-500 uppercase tracking-widest">{isSavingNotes ? 'Encrypting...' : 'Synced'}</span>
                                             {isSavingNotes ? <Loader2 className="w-3 h-3 text-primary animate-spin" /> : <Save className="w-4 h-4 text-emerald-500" />}
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <label className="text-[9px] font-black text-gray-400 uppercase tracking-widest italic ml-4">Tactical Observation</label>
                                        <textarea 
                                            placeholder="Document interview maneuvers and asset performance..."
                                            value={notes}
                                            onChange={(e) => saveNotes(e.target.value)}
                                            className="w-full bg-black/40 border border-white/10 rounded-[32px] p-6 text-sm font-bold text-white placeholder:text-gray-600 focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all h-64 resize-none"
                                        />
                                    </div>
                                    
                                    <div className="p-6 bg-primary/5 rounded-[32px] border border-primary/10">
                                        <p className="text-[9px] font-black text-primary uppercase tracking-widest mb-2 italic">Neural Suggestion</p>
                                        <p className="text-xs font-bold text-white leading-relaxed italic">"Candidate display strong proficiency in modular design. Probe deeper regarding their scalability strategy during Phase 2 deployment."</p>
                                    </div>

                                    {/* Whisper Activation */}
                                    <TacticalWhisperInput role={role} />
                                </motion.div>
                            )}

                            {/* Candidate Intel Panel */}
                            {role === 'candidate' && (
                                <div className="flex-grow bg-white/5 rounded-[40px] p-10 border border-white/5 space-y-8 overflow-y-auto scrollbar-hide">
                                     <div className="space-y-2">
                                         <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">Objective Matrix</h4>
                                         <h3 className="text-3xl font-black italic text-white tracking-tighter">Mission Intel</h3>
                                     </div>
                                     <div className="prose prose-invert prose-sm">
                                         <p className="text-gray-400 font-bold italic leading-relaxed">
                                            {interview.candidate_instructions || "No specific tactical instructions provided for this mission. Engage the primary interviewer for objective details."}
                                         </p>
                                     </div>
                                     <div className="grid grid-cols-2 gap-4">
                                          <div className="p-5 bg-black/40 rounded-3xl border border-white/10">
                                              <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Protocol Type</p>
                                              <p className="text-xs font-black text-white uppercase italic">{interview.type}</p>
                                          </div>
                                          <div className="p-5 bg-black/40 rounded-3xl border border-white/10">
                                              <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Duration</p>
                                              <p className="text-xs font-black text-white uppercase italic">{interview.duration_minutes}m Scan</p>
                                          </div>
                                     </div>
                                </div>
                            )}
                        </motion.div>
                    )}

                    {/* Shared Editor Area */}
                    {(activePanel === 'split' || activePanel === 'editor') && (
                        <motion.div 
                             initial={{ width: 0, opacity: 0 }}
                             animate={{ width: activePanel === 'split' ? "60%" : "100%", opacity: 1 }}
                             exit={{ width: 0, opacity: 0 }}
                             transition={{ type: "spring", stiffness: 100, damping: 20 }}
                             className="h-full p-8"
                        >
                            <SharedEditor 
                                interviewId={id} 
                                language={interview.type === 'technical' ? 'javascript' : 'markdown'} 
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </main>

            {/* Tactical Notifications */}
            {role === 'interviewer' && <WhisperFeed whispers={whispers} />}
        </div>
    );
}

function ViewButton({ active, icon, label, onClick }: { active: boolean, icon: React.ReactNode, label: string, onClick: () => void }) {
    return (
        <button 
            onClick={onClick}
            className={`px-5 py-2.5 rounded-xl flex items-center space-x-2 text-[9px] font-black uppercase tracking-widest transition-all ${
                active ? 'bg-primary text-white shadow-xl shadow-primary/20 scale-105' : 'text-gray-500 hover:text-white'
            }`}
        >
            {icon}
            <span>{label}</span>
        </button>
    );
}