"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    BrainCircuit, ShieldCheck, Plus, 
    Trash2, RefreshCcw, CheckCircle2, 
    XCircle, Filter, Search, 
    AlertCircle, Layers, Target,
    Info, Database
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function NeuralSeedingConsole() {
    const supabase = createClient();
    const [pools, setPools] = useState<any[]>([]);
    const [selectedSkill, setSelectedSkill] = useState<string | null>(null);
    const [unverifiedQuestions, setUnverifiedQuestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isGenerating, setIsGenerating] = useState(false);
    const [activeTab, setActiveTab] = useState<'pools' | 'verification'>('pools');

    useEffect(() => {
        const fetchPoolData = async () => {
            const { data } = await supabase
                .from("assessment_pool_metadata")
                .select("*")
                .order("skill_name", { ascending: true });
            
            if (data) setPools(data);
            setLoading(false);
        };

        fetchPoolData();
    }, [supabase]);

    useEffect(() => {
        if (selectedSkill) {
            const fetchUnverified = async () => {
                const { data } = await supabase
                    .from("assessment_questions")
                    .select("*, assessments(title)")
                    .eq("is_verified", false)
                    .ilike("assessments.title", `%${selectedSkill}%`);
                
                if (data) setUnverifiedQuestions(data);
            };
            fetchUnverified();
        }
    }, [selectedSkill, supabase]);

    const handleBulkGenerate = async (skill: string) => {
        setIsGenerating(true);
        try {
            // 1. Trigger AI Generation (Simulated for this MVP)
            const response = await fetch("/api/assessments/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ skill, count: 5 })
            });

            if (!response.ok) throw new Error("Bulk Sync Failed");
            const data = await response.json();

            // 2. Create a "Base Pool Assessment" if it doesn't exist or use the main one
            const { data: { user } } = await supabase.auth.getUser();
            
            // For now, we save these questions as generic unverified points
            const { data: poolAssessment } = await supabase
                    .from("assessments")
                    .select("id")
                    .eq("title", `Pool: ${skill}`)
                    .single();

            let targetId = poolAssessment?.id;
            if (!targetId) {
                const { data: newAss } = await supabase
                    .from("assessments")
                    .insert({ title: `Pool: ${skill}`, creator_id: user?.id, is_active: false })
                    .select()
                    .single();
                targetId = newAss?.id;
            }

            const questions = data.questions.map((q: any) => ({
                assessment_id: targetId,
                question_text: q.text,
                options: q.options,
                correct_answer: q.correctAnswer.toString(),
                explanation: q.explanation || "",
                is_verified: false
            }));

            await supabase.from("assessment_questions").insert(questions);
            
            setSelectedSkill(skill);
            setActiveTab('verification');
            // Refresh counts logic here
        } catch (error: any) {
            alert(`Pool Sync Error: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const verifyQuestion = async (id: string) => {
        await supabase.from("assessment_questions").update({ is_verified: true }).eq("id", id);
        setUnverifiedQuestions(prev => prev.filter(q => q.id !== id));
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-32">
            {/* Header */}
            <header className="flex flex-col space-y-4">
                <div className="flex items-center space-x-3 text-primary">
                     <Database className="w-6 h-6" />
                     <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">Pool Mastery Hub</span>
                </div>
                <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter uppercase leading-none">
                    Questions <span className="text-primary tracking-normal">Reservoir</span>
                </h1>
                <p className="text-gray-500 font-bold max-w-lg">Industrial-strength technical pool management and neural seeding console.</p>
            </header>

            {/* Navigation Tabs */}
            <div className="flex items-center space-x-8 border-b border-gray-100">
                <button 
                    onClick={() => setActiveTab('pools')}
                    className={`pb-6 text-sm font-black uppercase tracking-widest italic transition-all relative ${
                        activeTab === 'pools' ? "text-zinc-900" : "text-gray-400 hover:text-zinc-600"
                    }`}
                >
                    Management Grid
                    {activeTab === 'pools' && <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-1 bg-primary" />}
                </button>
                <button 
                    onClick={() => setActiveTab('verification')}
                    className={`pb-6 text-sm font-black uppercase tracking-widest italic transition-all relative ${
                        activeTab === 'verification' ? "text-zinc-900" : "text-gray-400 hover:text-zinc-600"
                    }`}
                >
                    Verification Queue
                    <span className="ml-2 px-2 py-0.5 bg-red-50 text-red-500 text-[8px] rounded-full">{unverifiedQuestions.length}</span>
                    {activeTab === 'verification' && <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-1 bg-primary" />}
                </button>
            </div>

            {activeTab === 'pools' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {pools.map((pool) => (
                        <div key={pool.id} className="bg-white border border-gray-100 rounded-[48px] p-8 space-y-8 shadow-sm group hover:border-primary/20 transition-all">
                            <div className="flex items-center justify-between">
                                <div className="p-4 bg-primary/5 text-primary rounded-[24px]">
                                    <Layers className="w-5 h-5" />
                                </div>
                                <span className="text-[8px] font-black uppercase tracking-widest text-gray-400">Node Status: Active</span>
                            </div>
                            
                            <div>
                                <h3 className="text-2xl font-black text-zinc-900 italic tracking-tight uppercase">{pool.skill_name}</h3>
                                <div className="grid grid-cols-2 gap-4 mt-6">
                                    <div className="bg-emerald-50 p-4 rounded-3xl">
                                        <p className="text-[8px] font-black text-emerald-600 uppercase tracking-widest mb-1">Verified</p>
                                        <p className="text-xl font-black text-emerald-700 italic">{pool.total_verified}</p>
                                    </div>
                                    <div className="bg-red-50 p-4 rounded-3xl">
                                        <p className="text-[8px] font-black text-red-600 uppercase tracking-widest mb-1">Queue</p>
                                        <p className="text-xl font-black text-red-700 italic">{pool.total_unverified}</p>
                                    </div>
                                </div>
                            </div>

                            <button 
                                onClick={() => handleBulkGenerate(pool.skill_name)}
                                disabled={isGenerating}
                                className="w-full py-4 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic hover:bg-primary transition-all flex items-center justify-center space-x-2 shadow-xl shadow-zinc-900/10"
                            >
                                <RefreshCcw className={`w-4 h-4 ${isGenerating ? "animate-spin" : ""}`} />
                                <span>Bulk Seed Node</span>
                            </button>
                        </div>
                    ))}

                    {/* New Skill Adder */}
                    <div className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-[48px] p-8 flex flex-col items-center justify-center text-center space-y-6">
                         <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center shadow-sm">
                             <Plus className="w-8 h-8 text-gray-400" />
                         </div>
                         <div className="space-y-2">
                            <h4 className="font-black italic text-zinc-900 uppercase">Initialize New Node</h4>
                            <p className="text-[10px] font-bold text-gray-400 italic">Expand the technical reservoir to include new disciplines.</p>
                         </div>
                         <button className="px-8 py-3 bg-white border border-gray-100 rounded-2xl text-[10px] font-black uppercase tracking-widest italic hover:bg-zinc-900 hover:text-white transition-all shadow-sm">
                             Add Discipline
                         </button>
                    </div>
                </div>
            ) : (
                <div className="space-y-8">
                    {unverifiedQuestions.map((q, idx) => (
                        <div key={q.id} className="bg-zinc-900 rounded-[48px] p-10 flex flex-col lg:flex-row items-center justify-between gap-10 group relative overflow-hidden">
                            <div className="relative z-10 flex-1 space-y-6">
                                <div className="flex items-center space-x-4">
                                     <span className="px-4 py-1.5 bg-primary/20 text-primary rounded-xl text-[8px] font-black uppercase tracking-widest italic">Review Required</span>
                                     <span className="text-[8px] font-black text-white/40 uppercase tracking-widest">Skill: {q.skill_name || 'Technical'}</span>
                                </div>
                                <h4 className="text-xl font-black text-white italic tracking-tight leading-relaxed">{q.question_text}</h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {q.options.map((opt: string, oi: number) => (
                                        <div key={oi} className={`p-4 rounded-[20px] text-[10px] font-bold italic ${
                                            q.correct_answer === oi.toString() ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" : "bg-white/5 text-white/40 border border-white/10"
                                        }`}>
                                            {opt}
                                        </div>
                                    ))}
                                </div>
                                {q.explanation && (
                                     <div className="p-6 bg-white/5 rounded-[32px] border border-white/5">
                                         <div className="flex items-center space-x-2 text-primary mb-2">
                                             <Info className="w-3 h-3" />
                                             <span className="text-[8px] font-black uppercase tracking-widest">Neural Reasoning</span>
                                         </div>
                                         <p className="text-[10px] text-white/60 font-bold italic leading-relaxed">{q.explanation}</p>
                                     </div>
                                )}
                            </div>

                            <div className="relative z-10 flex flex-row lg:flex-col items-center gap-4">
                                <button 
                                    onClick={() => verifyQuestion(q.id)}
                                    className="p-5 bg-emerald-500 text-white rounded-[28px] hover:scale-110 transition-all shadow-xl shadow-emerald-500/20"
                                >
                                    <CheckCircle2 className="w-6 h-6" />
                                </button>
                                <button className="p-5 bg-white/5 text-white/40 rounded-[28px] hover:bg-red-500 hover:text-white transition-all">
                                    <RefreshCcw className="w-6 h-6" />
                                </button>
                                <button className="p-5 bg-white/5 text-white/40 rounded-[28px] hover:bg-red-500 hover:text-white transition-all">
                                    <Trash2 className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="absolute right-0 top-0 w-64 h-full bg-primary/5 -skew-x-12 translate-x-20 pointer-events-none" />
                        </div>
                    ))}

                    {unverifiedQuestions.length === 0 && (
                        <div className="bg-white border-2 border-dashed border-gray-100 rounded-[56px] p-32 text-center space-y-6">
                            <div className="w-20 h-20 bg-emerald-50 text-emerald-500 rounded-full flex items-center justify-center mx-auto">
                                <ShieldCheck className="w-10 h-10" />
                            </div>
                            <h3 className="text-2xl font-black text-zinc-900 italic tracking-tight uppercase">Reservoir Balanced</h3>
                            <p className="text-gray-500 font-bold max-w-sm mx-auto italic">No unverified questions currently in the queue. All technical nodes are vetted and operational.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
