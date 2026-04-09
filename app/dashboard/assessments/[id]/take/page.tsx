"use client";

import { useEffect, useState, use, Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Clock, BrainCircuit, CheckCircle2, 
    XCircle, ArrowRight, ShieldCheck,
    AlertCircle, ChevronRight, Send,
    FileText, Target, Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter, useSearchParams } from "next/navigation";
import { updateCombinedNeuralScore } from "@/lib/supabase/scoring";
import { issueNeuralBadge } from "@/lib/supabase/achievements";

function AssessmentFocusedContent({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const searchParams = useSearchParams();
    const applicationId = searchParams.get("applicationId");
    const supabase = createClient();
    
    const [loading, setLoading] = useState(true);
    const [assessment, setAssessment] = useState<any>(null);
    const [questions, setQuestions] = useState<any[]>([]);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [status, setStatus] = useState<"idle" | "active" | "submitting" | "completed">("idle");
    const [attemptId, setAttemptId] = useState<string | null>(null);
    const [timeLeft, setTimeLeft] = useState(0); // seconds
    const [violations, setViolations] = useState(0);

    // 1. Initial Data Fetch & Attempt Initialization
    useEffect(() => {
        const startSession = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            // Fetch Assessment
            const { data: aData, error: aError } = await supabase
                .from("assessments")
                .select("*")
                .eq("id", id)
                .single();
            
            if (aError || !aData) {
                console.error("Assessment discovery failed.");
                return;
            }
            setAssessment(aData);
            setTimeLeft(aData.duration_minutes * 60);

            // Fetch Questions (Only if attempt starts or is active)
            const { data: qData } = await supabase
                .from("assessment_questions")
                .select("*")
                .eq("assessment_id", id)
                .order("order_index", { ascending: true });
            
            if (qData) setQuestions(qData);
            setLoading(false);
        };

        startSession();
    }, [id, supabase, router]);

    // 2. Mission Clock
    useEffect(() => {
        if (status !== "active" || timeLeft <= 0) return;

        const timer = setInterval(() => {
            setTimeLeft(prev => {
                if (prev <= 1) {
                    handleAutoSubmit();
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);

        return () => clearInterval(timer);
    }, [status, timeLeft]);

    // 3. Basic Proctoring (Tab Switch Detection)
    useEffect(() => {
        if (status !== "active") return;

        const handleBlur = () => setViolations(prev => prev + 1);
        
        window.addEventListener("blur", handleBlur);
        return () => window.removeEventListener("blur", handleBlur);
    }, [status]);

    const initializeAttempt = async () => {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        setStatus("active");
        const { data: attempt, error } = await supabase
            .from("assessment_attempts")
            .insert({
                assessment_id: id,
                candidate_id: user.id,
                job_application_id: applicationId,
                status: "started"
            })
            .select()
            .single();
        
        if (attempt) setAttemptId(attempt.id);
    };

    const handleAnswerSelect = (questionId: string, optionIndex: string) => {
        setAnswers(prev => ({ ...prev, [questionId]: optionIndex }));
    };

    const handleAutoSubmit = () => {
        if (status === "active") submitProtocol("timed_out");
    };

    const submitProtocol = async (finalStatus: "completed" | "timed_out" = "completed") => {
        if (!attemptId) return;
        setStatus("submitting");

        // Calculate raw score
        let score = 0;
        let totalPoints = 0;
        questions.forEach(q => {
            totalPoints += q.points;
            if (answers[q.id] === q.correct_answer) {
                score += q.points;
            }
        });

        const percentageScore = Math.round((score / totalPoints) * 100);

        const { error } = await supabase
            .from("assessment_attempts")
            .update({
                answers,
                score: percentageScore,
                total_points: totalPoints,
                status: finalStatus,
                completed_at: new Date().toISOString(),
                metadata: {
                    tab_switch_violations: violations,
                    final_time_remaining: timeLeft
                }
            })
            .eq("id", attemptId);

        if (!error) {
            // 1. Update combined score if for a job mission
            if (applicationId) {
                await updateCombinedNeuralScore(applicationId);
            }

            // 2. Issuance of Neural Badge (Personal Account achievement)
            await issueNeuralBadge(attemptId);
            
            // 3. Redirect to Results Dashboard for immediate feedback
            router.push(`/dashboard/assessments/results/${attemptId}`);
        }
    };

    if (loading) return (
        <div className="min-h-screen bg-white flex items-center justify-center">
             <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full"
             />
        </div>
    );

    if (status === "idle") return (
        <div className="max-w-4xl mx-auto min-h-screen flex items-center justify-center p-8">
            <motion.div 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-white border border-gray-100 rounded-[56px] p-16 shadow-2xl text-center space-y-10 relative overflow-hidden"
            >
                <div className="relative z-10 space-y-8">
                    <div className="p-6 bg-primary/10 text-primary rounded-[32px] inline-flex items-center justify-center mb-4">
                        <BrainCircuit className="w-16 h-16" />
                    </div>
                    <div>
                        <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter uppercase leading-none mb-4">
                            Protocol <span className="text-primary tracking-normal">{assessment.title}</span>
                        </h1>
                        <p className="text-gray-500 font-bold max-w-lg mx-auto italic">
                            {assessment.description || "You are about to initiate a neural vetting cycle. This environment is monitored for focused performance."}
                        </p>
                    </div>

                    <div className="grid grid-cols-3 gap-6">
                         <div className="p-6 bg-gray-50 rounded-[32px]">
                             <Clock className="w-6 h-6 text-primary mx-auto mb-2" />
                             <p className="text-[10px] font-black uppercase tracking-widest text-gray-400">Duration</p>
                             <p className="text-xl font-black text-zinc-900 italic">{assessment.duration_minutes}m</p>
                         </div>
                         <div className="p-6 bg-gray-50 rounded-[32px]">
                             <FileText className="w-6 h-6 text-primary mx-auto mb-2" />
                             <p className="text-[10px] font-black uppercase tracking-widest text-gray-400">Queries</p>
                             <p className="text-xl font-black text-zinc-900 italic">{questions.length}</p>
                         </div>
                         <div className="p-6 bg-gray-50 rounded-[32px]">
                             <ShieldCheck className="w-6 h-6 text-primary mx-auto mb-2" />
                             <p className="text-[10px] font-black uppercase tracking-widest text-gray-400">Security</p>
                             <p className="text-xl font-black text-zinc-900 italic">High</p>
                         </div>
                    </div>

                    <button 
                         onClick={initializeAttempt}
                         className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-[10px] uppercase tracking-[0.2em] italic hover:scale-105 transition-all shadow-2xl shadow-zinc-900/20"
                    >
                         Initialize Vetting Phase
                    </button>
                </div>
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] rounded-full translate-x-1/3 -translate-y-1/3 pointer-events-none" />
            </motion.div>
        </div>
    );

    if (status === "completed") return (
        <div className="max-w-4xl mx-auto min-h-screen flex items-center justify-center p-8">
             <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white border border-gray-100 rounded-[56px] p-20 shadow-2xl text-center space-y-10"
             >
                 <div className="p-6 bg-emerald-50 text-emerald-500 rounded-[32px] inline-flex items-center justify-center">
                     <CheckCircle2 className="w-16 h-16" />
                 </div>
                 <div className="space-y-4">
                     <h2 className="text-4xl font-black font-display text-zinc-900 italic tracking-tighter uppercase leading-none">Transmission Completed</h2>
                     <p className="text-gray-500 font-bold italic">Your neural metrics have been successfully archived and synced with the mission controller.</p>
                 </div>
                 <button 
                    onClick={() => router.push("/dashboard")}
                    className="px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-widest italic hover:scale-105 transition-all"
                 >
                    Return to Mission Hub
                 </button>
             </motion.div>
        </div>
    );

    const q = questions[currentQuestionIndex];
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    return (
        <div className="min-h-screen bg-white flex flex-col">
             {/* Mission Bar */}
             <header className="h-24 px-8 md:px-16 border-b border-gray-100 flex items-center justify-between sticky top-0 bg-white/80 backdrop-blur-xl z-50">
                 <div className="flex items-center space-x-6">
                      <div className="w-12 h-12 bg-zinc-900 rounded-2xl flex items-center justify-center font-black text-white italic">
                          H
                      </div>
                      <div className="hidden md:block">
                          <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Active Blueprint</p>
                          <p className="text-xs font-black text-zinc-900 italic tracking-tight">{assessment.title}</p>
                      </div>
                 </div>

                 <div className="flex items-center space-x-12">
                     <div className="flex items-center space-x-4">
                          <div className={`p-3 rounded-xl flex items-center space-x-3 ${timeLeft < 300 ? "bg-red-50 text-red-500 animate-pulse" : "bg-primary/5 text-primary"}`}>
                              <Clock className="w-5 h-5" />
                              <span className="text-lg font-black italic tracking-tighter">
                                  {minutes}:{seconds.toString().padStart(2, "0")}
                              </span>
                          </div>
                          <div className="hidden lg:flex flex-col text-right">
                               <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Mission End</p>
                               <p className="text-xs font-bold text-zinc-900 italic uppercase">Auto-Submit Protocol</p>
                          </div>
                     </div>

                     <button 
                        onClick={() => submitProtocol()}
                        className="px-8 py-3 bg-zinc-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-emerald-600 transition-all shadow-xl"
                    >
                         Finalize
                     </button>
                 </div>
             </header>

             {/* Progress Strip */}
             <div className="h-1.5 w-full bg-gray-50 overflow-hidden">
                 <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
                    className="h-full bg-primary"
                 />
             </div>

             <main className="flex-grow flex flex-col md:flex-row max-w-7xl mx-auto w-full p-8 md:p-16 gap-16">
                 {/* Question Content */}
                 <div className="flex-grow space-y-12">
                     <div className="space-y-6">
                         <div className="flex items-center space-x-3">
                              <span className="px-4 py-1.5 bg-gray-900 text-white text-[10px] font-black uppercase tracking-widest rounded-xl italic">Query Node {currentQuestionIndex + 1}</span>
                              <span className="text-[10px] font-black text-gray-300 uppercase tracking-widest">• Total Vectors {questions.length}</span>
                         </div>
                         <h3 className="text-3xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-tight">
                            {q?.question_text}
                         </h3>
                     </div>

                     <div className="grid grid-cols-1 gap-4">
                         {(q?.options || []).map((opt: string, idx: number) => {
                             const isSelected = answers[q.id] === idx.toString();
                             return (
                                 <button 
                                    key={idx}
                                    onClick={() => handleAnswerSelect(q.id, idx.toString())}
                                    className={`group flex items-center justify-between p-8 rounded-[32px] border-2 transition-all text-left ${
                                        isSelected 
                                        ? "bg-primary/5 border-primary shadow-xl shadow-primary/5" 
                                        : "bg-white border-gray-100 hover:border-primary/20"
                                    }`}
                                 >
                                     <div className="flex items-center space-x-6">
                                         <div className={`w-10 h-10 rounded-2xl border-2 flex items-center justify-center font-black text-xs transition-all ${
                                             isSelected ? "bg-primary border-primary text-white" : "bg-gray-50 border-gray-200 text-gray-400 group-hover:border-primary/40"
                                         }`}>
                                             {String.fromCharCode(65 + idx)}
                                         </div>
                                         <span className={`text-lg font-bold italic ${isSelected ? "text-primary" : "text-gray-500"}`}>{opt}</span>
                                     </div>
                                     {isSelected && <CheckCircle2 className="w-6 h-6 text-primary" />}
                                 </button>
                             );
                         })}
                     </div>

                     {/* Navigation */}
                     <div className="flex items-center justify-between pt-12 border-t border-gray-50">
                         <button 
                            disabled={currentQuestionIndex === 0}
                            onClick={() => setCurrentQuestionIndex(prev => prev - 1)}
                            className="px-8 py-4 bg-white border border-gray-100 rounded-3xl font-black text-[10px] uppercase tracking-widest text-gray-400 hover:text-zinc-900 hover:border-zinc-900 disabled:opacity-30 disabled:pointer-events-none transition-all"
                        >
                            Previous Node
                         </button>
                         
                         {currentQuestionIndex === questions.length - 1 ? (
                             <button 
                                onClick={() => submitProtocol()}
                                className="px-12 py-4 bg-emerald-500 text-white rounded-3xl font-black text-[10px] uppercase tracking-[0.2em] italic hover:scale-105 transition-all shadow-xl shadow-emerald-500/20 flex items-center space-x-3"
                             >
                                 <Target className="w-4 h-4" />
                                 <span>Complete Mission</span>
                             </button>
                         ) : (
                             <button 
                                onClick={() => setCurrentQuestionIndex(prev => prev + 1)}
                                className="px-12 py-4 bg-primary text-white rounded-3xl font-black text-[10px] uppercase tracking-[0.2em] italic hover:scale-105 transition-all shadow-xl shadow-primary/20 flex items-center space-x-3"
                             >
                                 <span>Next Phase</span>
                                 <ArrowRight className="w-4 h-4" />
                             </button>
                         )}
                     </div>
                 </div>

                 {/* Vector Map (Desktop Sidebar) */}
                 <div className="hidden lg:block w-72 space-y-10">
                     <div className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm">
                         <h4 className="text-[10px] font-black text-zinc-900 uppercase tracking-widest italic mb-6">Neural Vector Map</h4>
                         <div className="grid grid-cols-4 gap-3">
                             {questions.map((_, idx) => (
                                 <button
                                     key={idx}
                                     onClick={() => setCurrentQuestionIndex(idx)}
                                     className={`w-full aspect-square rounded-xl text-[10px] font-black transition-all border-2 ${
                                         currentQuestionIndex === idx 
                                         ? "bg-zinc-900 text-white border-zinc-900" 
                                         : answers[questions[idx].id] 
                                             ? "bg-primary/5 text-primary border-primary/20" 
                                             : "bg-white text-gray-300 border-gray-100 hover:border-primary/20"
                                     }`}
                                 >
                                     {idx + 1}
                                 </button>
                             ))}
                         </div>
                     </div>

                     <div className="bg-primary/5 rounded-[40px] p-8 space-y-4 border border-primary/10">
                          <div className="flex items-center space-x-3 text-primary">
                              <ShieldCheck className="w-5 h-5" />
                              <span className="text-[10px] font-black uppercase tracking-widest italic">Security Protocol</span>
                          </div>
                          <p className="text-[10px] text-primary/60 font-medium italic leading-relaxed">Focus mode is active. Tab synchronization and exit protocols are monitored.</p>
                     </div>
                 </div>
             </main>
        </div>
    );
}

export default function AssessmentFocusedPage({ params }: { params: Promise<{ id: string }> }) {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-white flex items-center justify-center">
                 <Loader2 className="w-12 h-12 animate-spin text-primary" />
            </div>
        }>
            <AssessmentFocusedContent params={params} />
        </Suspense>
    );
}
