"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    CheckCircle2, XCircle, Clock, 
    Target, BrainCircuit, Trophy, 
    ArrowRight, RotateCcw, ChevronLeft,
    ShieldCheck, AlertCircle, Info
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

export default function AssessmentResultsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id: attemptId } = use(params);
    const supabase = createClient();
    const router = useRouter();
    
    const [attempt, setAttempt] = useState<any>(null);
    const [assessment, setAssessment] = useState<any>(null);
    const [questions, setQuestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchResults = async () => {
            // 1. Fetch Attempt
            const { data: att, error: attErr } = await supabase
                .from("assessment_attempts")
                .select("*")
                .eq("id", attemptId)
                .single();

            if (attErr || !att) {
                console.error("Results Sync Failed:", attErr);
                setLoading(false);
                return;
            }

            setAttempt(att);

            // 2. Fetch Assessment & Questions
            const { data: ass, error: assErr } = await supabase
                .from("assessments")
                .select("*")
                .eq("id", att.assessment_id)
                .single();

            const { data: qs, error: qsErr } = await supabase
                .from("assessment_questions")
                .select("*")
                .eq("assessment_id", att.assessment_id)
                .order("order_index", { ascending: true });

            if (ass) setAssessment(ass);
            if (qs) setQuestions(qs);
            setLoading(false);
        };

        fetchResults();
    }, [attemptId, supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
             <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!attempt || !assessment) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 space-y-6">
             <AlertCircle className="w-16 h-16 text-red-500" />
             <h2 className="text-2xl font-black italic">Neural Link Severed</h2>
             <p className="text-gray-500 font-bold">The requested mission results could not be indexed.</p>
             <Link href="/dashboard" className="px-8 py-4 bg-zinc-900 text-white rounded-2xl font-black italic">Return to Base</Link>
        </div>
    );

    const score = parseFloat(attempt.score);
    const passed = score >= assessment.passing_score;

    return (
        <div className="max-w-5xl mx-auto space-y-12 pb-32 pt-8 px-4">
            {/* Header Navigation */}
            <div className="flex items-center justify-between">
                <Link href="/dashboard/achievements" className="flex items-center space-x-2 text-[10px] font-black text-gray-400 uppercase tracking-widest hover:text-primary transition-all group">
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Trophy Case</span>
                </Link>
                <div className="flex items-center space-x-2 text-[10px] font-black text-primary uppercase tracking-widest italic">
                    <ShieldCheck className="w-4 h-4" />
                    <span>Neural Verified Result</span>
                </div>
            </div>

            {/* Hero Result Section */}
            <section className={`rounded-[56px] p-12 md:p-20 text-center relative overflow-hidden shadow-2xl ${
                passed 
                ? "bg-emerald-500 text-white shadow-emerald-500/20" 
                : "bg-zinc-900 text-white shadow-zinc-900/20"
            }`}>
                <div className="relative z-10 flex flex-col items-center space-y-8">
                    <div className="p-6 bg-white/20 backdrop-blur-xl rounded-[40px] inline-flex">
                        {passed ? <Trophy className="w-16 h-16" /> : <BrainCircuit className="w-16 h-16" />}
                    </div>
                    
                    <div className="space-y-2">
                         <h1 className="text-5xl md:text-7xl font-black font-display italic tracking-tighter uppercase leading-none">
                            {passed ? (
                                <>Mission <br className="md:hidden"/> Accomplished</>
                            ) : (
                                <>Analysis <br className="md:hidden"/> Incomplete</>
                            )}
                         </h1>
                         <p className="text-white/60 font-black italic uppercase tracking-[0.2em]">{assessment.title}</p>
                    </div>

                    {/* Score Circle */}
                    <div className="relative w-48 h-48">
                        <svg className="w-full h-full transform -rotate-90">
                            <circle cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="12" fill="none" className="opacity-20" />
                            <motion.circle 
                                cx="96" cy="96" r="88" stroke="currentColor" strokeWidth="12" fill="none" 
                                strokeDasharray="552"
                                initial={{ strokeDashoffset: 552 }}
                                animate={{ strokeDashoffset: 552 - (552 * score / 100) }}
                                transition={{ duration: 1.5, ease: "easeOut" }}
                                className="opacity-100"
                            />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                            <span className="text-5xl font-black font-display italic leading-none">{score}%</span>
                            <span className="text-[10px] font-black uppercase tracking-widest opacity-60 mt-1">Final Index</span>
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-center gap-6">
                         {!passed && (
                            <Link 
                                href={`/dashboard/assessments/${assessment.id}/take`}
                                className="px-10 py-5 bg-white text-zinc-900 rounded-[32px] font-black text-sm uppercase tracking-widest italic hover:scale-105 transition-all shadow-xl"
                            >
                                <RotateCcw className="w-4 h-4 inline-block mr-2" />
                                Retake Mission
                            </Link>
                         )}
                         <Link 
                            href="/dashboard/achievements"
                            className="px-10 py-5 border border-white/20 hover:bg-white/10 rounded-[32px] font-black text-sm uppercase tracking-widest italic transition-all"
                         >
                            View Badges
                         </Link>
                    </div>
                </div>

                {/* Aesthetic Background */}
                <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
                <div className="absolute -bottom-10 -right-10 w-64 h-64 bg-white/5 blur-[80px] rounded-full pointer-events-none" />
            </section>

            {/* Detailed Performance Sequence */}
            <div className="space-y-8">
                <div className="flex items-center justify-between px-6">
                    <h2 className="text-3xl font-black text-zinc-900 italic tracking-tight uppercase">Neural Sequence Breakdown</h2>
                    <div className="hidden md:flex items-center space-x-6 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                         <div className="flex items-center space-x-2">
                             <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                             <span>Correct</span>
                         </div>
                         <div className="flex items-center space-x-2">
                             <XCircle className="w-4 h-4 text-red-500" />
                             <span>Incorrect</span>
                         </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    {questions.map((q, idx) => {
                        const userAnswer = attempt.answers?.[q.id];
                        const isCorrect = userAnswer === q.correct_answer;
                        
                        return (
                            <motion.div 
                                key={q.id}
                                initial={{ opacity: 0, x: -20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: idx * 0.1 }}
                                className="bg-white border border-gray-100 rounded-[48px] p-8 md:p-12 shadow-sm space-y-8 relative overflow-hidden group"
                            >
                                <div className="flex flex-col md:flex-row md:items-start justify-between gap-8">
                                    <div className="flex items-start space-x-6 md:space-x-10">
                                        <div className={`w-14 h-14 min-w-[56px] rounded-[24px] flex items-center justify-center font-black text-xl italic ${
                                            isCorrect ? "bg-emerald-500 text-white" : "bg-red-500 text-white"
                                        }`}>
                                            {isCorrect ? <CheckCircle2 className="w-6 h-6" /> : <XCircle className="w-6 h-6" />}
                                        </div>
                                        <div className="space-y-4">
                                            <h4 className="text-xl md:text-2xl font-black text-zinc-900 italic tracking-tight">{q.question_text}</h4>
                                            
                                            {/* Options Grid */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {q.options.map((opt: string, oIdx: number) => {
                                                    const isSelected = userAnswer === oIdx.toString();
                                                    const isRight = q.correct_answer === oIdx.toString();
                                                    
                                                    return (
                                                        <div 
                                                            key={oIdx}
                                                            className={`p-5 rounded-2xl border text-sm font-bold flex items-center justify-between ${
                                                                isRight 
                                                                ? "bg-emerald-50 border-emerald-500 text-emerald-700" 
                                                                : isSelected && !isRight
                                                                  ? "bg-red-50 border-red-500 text-red-700"
                                                                  : "bg-gray-50 border-gray-100 text-gray-500"
                                                            }`}
                                                        >
                                                            <span>{opt}</span>
                                                            {isRight && <CheckCircle2 className="w-4 h-4 ml-2" />}
                                                            {isSelected && !isRight && <XCircle className="w-4 h-4 ml-2" />}
                                                        </div>
                                                    );
                                                })}
                                            </div>

                                            {/* Neural Explanation */}
                                            {q.explanation && (
                                                <div className="mt-8 p-8 bg-zinc-900 rounded-[40px] relative overflow-hidden group/expl">
                                                     <div className="relative z-10">
                                                        <div className="flex items-center space-x-3 text-primary mb-4">
                                                            <Info className="w-5 h-5" />
                                                            <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">Neural Reasoning</span>
                                                        </div>
                                                        <p className="text-white/80 font-bold text-sm leading-relaxed italic">
                                                            {q.explanation}
                                                        </p>
                                                     </div>
                                                     <div className="absolute right-0 top-0 w-32 h-full bg-primary/5 -skew-x-12 translate-x-20" />
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="text-right hidden lg:block min-w-[120px]">
                                        <p className="text-3xl font-black text-zinc-900 italic tracking-tighter">+{q.points}</p>
                                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mt-1">Neural Points</p>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>

            {/* Footer Actions */}
            <div className="flex justify-center space-x-6">
                <Link 
                    href={`/dashboard/assessments/${assessment.id}/take`}
                    className="px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-[0.2em] italic hover:scale-105 transition-all shadow-2xl"
                >
                    Retake Mission
                </Link>
                <Link 
                    href="/dashboard"
                    className="px-12 py-5 bg-white border border-gray-100 text-zinc-900 rounded-[32px] font-black text-xs uppercase tracking-[0.2em] italic hover:bg-gray-50 transition-all"
                >
                    Back to Base
                </Link>
            </div>
        </div>
    );
}
