"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    BrainCircuit, ShieldCheck, Zap, 
    MessageSquare, AlertCircle, Loader2,
    ChevronRight, Terminal, Timer, ArrowRight,
    Play, CheckCircle2, Trophy
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import SharedEditor from "@/components/interviews/SharedEditor";
import ConsentModal from "@/components/interviews/ConsentModal";
import AvaAgentRoom from "@/components/interviews/AvaAgentRoom";

export default function PracticeRoomPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    
    const [session, setSession] = useState<any>(null);
    const [questions, setQuestions] = useState<any[]>([]);
    const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
    const [loading, setLoading] = useState(true);
    const [hasConsented, setHasConsented] = useState(false);
    const [timeRemaining, setTimeRemaining] = useState(1800); // 30m
    const [voiceToken, setVoiceToken] = useState<string | null>(null);
    const [livekitUrl, setLivekitUrl] = useState<string | null>(null);

    useEffect(() => {
        const fetchSession = async () => {
            const { data: sessData, error: sessError } = await supabase
                .from("interview_practice_sessions")
                .select(`
                    *,
                    questions:practice_questions(*)
                `)
                .eq("id", id)
                .single();

            if (sessData) {
                setSession(sessData);
                setQuestions(sessData.questions || []);

                // If voice mission, fetch token
                if (sessData.type === 'voice') {
                    const { data: { user } } = await supabase.auth.getUser();
                    const res = await fetch(`/api/interviews/ava/token?room=${id}&username=${user?.full_name?.replace(/\s/g, '_') || 'Candidate'}`);
                    const { token, url } = await res.json();
                    setVoiceToken(token);
                    setLivekitUrl(url);
                }
            }
            setLoading(false);
        };

        fetchSession();
    }, [id, supabase]);

    const currentQuestion = questions[currentQuestionIdx];

    useEffect(() => {
        if (hasConsented && timeRemaining > 0) {
            const timer = setInterval(() => setTimeRemaining(t => t - 1), 1000);
            return () => clearInterval(timer);
        }
    }, [hasConsented, timeRemaining]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleCompleteSession = async () => {
        setLoading(true);
        await supabase
            .from("interview_practice_sessions")
            .update({ status: "completed", completed_at: new Date().toISOString() })
            .eq("id", id);
        
        // Trigger AI Evaluator for Practice
        await supabase.functions.invoke('interviews-evaluator', {
            body: { sessionId: id, mode: 'practice' }
        });

        router.push(`/dashboard/interviews`);
    };

    if (loading) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[#0c0c0c]">
            <Loader2 className="w-12 h-12 text-primary animate-spin" />
        </div>
    );

    if (session?.type === 'voice' && voiceToken && livekitUrl) {
        return (
            <AvaAgentRoom 
                roomId={id} 
                token={voiceToken} 
                url={livekitUrl} 
                onComplete={() => router.push('/dashboard/interviews')} 
            />
        );
    }

    return (
        <div className="bg-[#0c0c0c] text-white h-screen flex flex-col overflow-hidden relative">
            <ConsentModal 
                isOpen={!hasConsented} 
                onAccept={() => setHasConsented(true)}
                onDecline={() => router.push('/dashboard/interviews')}
            />

            {/* Header */}
            <header className="h-20 bg-black/60 backdrop-blur-3xl border-b border-white/5 flex items-center justify-between px-10 shrink-0 z-50">
                <div className="flex items-center space-x-8">
                    <button 
                        onClick={() => router.push('/dashboard/interviews')}
                        className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5 group"
                    >
                        <ChevronRight className="w-5 h-5 text-gray-400 rotate-180" />
                    </button>
                    <div>
                         <div className="flex items-center space-x-3 mb-1">
                             <div className="p-1 bg-amber-500/20 rounded-md">
                                 <Zap className="w-3 h-3 text-amber-500" />
                             </div>
                             <span className="text-[8px] font-black text-amber-500 uppercase tracking-[0.4em] italic">Neural Simulator v2.0</span>
                         </div>
                         <h2 className="text-lg font-black italic tracking-tighter text-white uppercase leading-none">
                            Training Payload: {session.focus_areas[0] || 'General Intelligence'}
                         </h2>
                    </div>
                </div>

                <div className="flex items-center space-x-6">
                    <div className="flex items-center space-x-3 bg-white/5 px-6 py-3 rounded-2xl border border-white/5">
                        <Timer className="w-4 h-4 text-primary" />
                        <span className="text-sm font-black text-white tabular-nums tracking-widest">{formatTime(timeRemaining)}</span>
                    </div>

                    <button 
                        onClick={handleCompleteSession}
                        className="px-8 py-3.5 bg-zinc-900 text-white border border-white/10 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] italic hover:bg-primary transition-all shadow-2xl"
                    >
                        De-initialize Simulator
                    </button>
                </div>
            </header>

            {/* Simulation Surface */}
            <main className="flex-grow relative flex">
                 <div className="w-1/3 h-full border-r border-white/5 p-10 overflow-y-auto scrollbar-hide flex flex-col space-y-10">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-4">
                             <div className="p-3 bg-primary/10 text-primary rounded-2xl border border-primary/20">
                                 <BrainCircuit className="w-6 h-6" />
                             </div>
                             <div>
                                 <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none mb-1">Objective Vector</p>
                                 <h4 className="text-xl font-black italic text-white uppercase tracking-tighter">Question {currentQuestionIdx + 1} of {questions.length || 0}</h4>
                             </div>
                        </div>

                        <div className="p-8 bg-white/5 rounded-[40px] border border-white/10 relative overflow-hidden group">
                             <p className="text-lg font-bold text-white italic leading-relaxed relative z-10">
                                 {currentQuestion?.prompt || "Awaiting neural transmission..."}
                             </p>
                             <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                 <MessageSquare className="w-20 h-20 text-white" />
                             </div>
                        </div>

                        {questions.length > 1 && (
                            <div className="flex space-x-4">
                                <button 
                                    className="flex-1 py-4 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all font-black text-[10px] uppercase tracking-widest text-gray-400 disabled:opacity-30"
                                    disabled={currentQuestionIdx === 0}
                                    onClick={() => setCurrentQuestionIdx(i => i - 1)}
                                >
                                    Previous Vector
                                </button>
                                <button 
                                    className="flex-1 py-4 bg-primary text-white rounded-2xl hover:scale-105 transition-all font-black text-[10px] uppercase tracking-widest italic flex items-center justify-center space-x-2 shadow-xl shadow-primary/20"
                                    disabled={currentQuestionIdx === questions.length - 1}
                                    onClick={() => setCurrentQuestionIdx(i => i + 1)}
                                >
                                    <span>Advance Protocol</span>
                                    <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="bg-amber-500/5 rounded-[32px] p-8 border border-amber-500/10 space-y-4">
                        <div className="flex items-center space-x-3 text-amber-500">
                             <AlertCircle className="w-5 h-5" />
                             <h4 className="text-[10px] font-black uppercase tracking-widest italic">Simulator Directives</h4>
                        </div>
                        <ul className="space-y-3">
                            <li className="flex items-start space-x-3 text-xs font-bold text-gray-400 italic">
                                <span className="text-primary mt-1">01.</span>
                                <span>Complete the technical prompt in the adjacent terminal.</span>
                            </li>
                            <li className="flex items-start space-x-3 text-xs font-bold text-gray-400 italic">
                                <span className="text-primary mt-1">02.</span>
                                <span>Synthetic scoring based on complexity and optimization.</span>
                            </li>
                            <li className="flex items-start space-x-3 text-xs font-bold text-gray-400 italic">
                                <span className="text-primary mt-1">03.</span>
                                <span>Protocol auto-finalizes when timer reaches zero.</span>
                            </li>
                        </ul>
                    </div>
                 </div>

                 <div className="flex-1 h-full p-8 bg-black">
                     <SharedEditor interviewId={`practice-${id}`} initialCode="// Initialize simulation logic here..." />
                 </div>
            </main>
        </div>
    );
}
