"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Target, Zap, Rocket, Check, X, ChevronRight, Loader2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface PracticeSetupProps {
    isOpen: boolean;
    onClose: () => void;
    onComplete: (sessionId: string) => void;
}

export default function PracticeSetup({ isOpen, onClose, onComplete }: PracticeSetupProps) {
    const supabase = createClient();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [difficulty, setDifficulty] = useState("intermediate");
    const [missionType, setMissionType] = useState("standard");
    const [focusAreas, setFocusAreas] = useState<string[]>([]);

    const MISSION_TYPES = [
        { id: 'standard', label: 'Standard Simulator', icon: <Target className="w-4 h-4" /> },
        { id: 'voice', label: 'Ava Voice Protocol', icon: <BrainCircuit className="w-4 h-4" /> },
    ];

    const FOCUS_OPTIONS = [
        "Frontend React", "System Design", "Backend Node.js", 
        "Data Structures", "Behavioral", "DevOps/Cloud"
    ];

    const toggleFocus = (area: string) => {
        setFocusAreas(prev => 
            prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
        );
    };

    const handleInitialize = async () => {
        setLoading(true);
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        try {
            // 1. Create Practice Session
            const { data: session, error: sessError } = await supabase
                .from("interview_practice_sessions")
                .insert({
                    candidate_id: user.id,
                    difficulty,
                    focus_areas: focusAreas,
                    status: "in_progress",
                    type: missionType
                })
                .select()
                .single();

            if (sessError) throw sessError;

            // 2. Trigger AI Generator for Practice Questions (Vercel API)
            const genRes = await fetch('/api/interviews/generator', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    session_id: session.id,
                    mode: 'practice',
                    difficulty,
                    focus_areas: focusAreas
                })
            });

            if (!genRes.ok) {
                const errData = await genRes.json();
                throw new Error(errData.error || "AI Generation failed");
            }

            onComplete(session.id);
        } catch (error: any) {
            console.error("Initialization Failed:", error.message || error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-xl"
                    />

                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-2xl bg-white rounded-[48px] shadow-2xl overflow-hidden"
                    >
                        {loading ? (
                            <div className="p-24 text-center space-y-8">
                                <div className="relative w-24 h-24 mx-auto">
                                    <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
                                    <div className="absolute inset-0 border-t-4 border-primary rounded-full animate-spin" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-3xl font-black text-zinc-900 italic tracking-tighter uppercase">Calibrating Simulator</h3>
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic animate-pulse">Synthesizing Neural Challenges...</p>
                                </div>
                            </div>
                        ) : (
                            <div className="p-12 space-y-10">
                                <header className="flex items-center justify-between">
                                    <div className="space-y-1">
                                        <h3 className="text-3xl font-black text-zinc-900 italic tracking-tighter">Command <span className="text-primary italic">Initialization</span></h3>
                                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none">Training Simulator Configuration</p>
                                    </div>
                                    <button onClick={onClose} className="p-3 bg-gray-50 rounded-2xl text-gray-400 hover:text-red-500 transition-colors">
                                        <X className="w-6 h-6" />
                                    </button>
                                </header>

                                {step === 1 && (
                                    <motion.div 
                                        initial={{ opacity: 0, x: 20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        className="space-y-8"
                                    >
                                        <section className="space-y-4">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                                <Zap className="w-3 h-3 text-primary" />
                                                <span>Mission Protocol</span>
                                            </label>
                                            <div className="grid grid-cols-2 gap-4">
                                                {MISSION_TYPES.map(m => (
                                                    <button
                                                        key={m.id}
                                                        onClick={() => setMissionType(m.id)}
                                                        className={`p-4 rounded-3xl flex items-center space-x-3 transition-all border ${
                                                            missionType === m.id ? 'bg-zinc-900 text-white border-zinc-900 shadow-xl' : 'bg-gray-50 text-gray-400 border-gray-100 hover:bg-white'
                                                        }`}
                                                    >
                                                        {m.icon}
                                                        <span className="text-[10px] font-black uppercase tracking-widest italic">{m.label}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        </section>

                                        <section className="space-y-4">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                                <Target className="w-3 h-3 text-primary" />
                                                <span>Target Difficulty</span>
                                            </label>
                                            <div className="grid grid-cols-3 gap-4">
                                                {['beginner', 'intermediate', 'advanced'].map(d => (
                                                    <button
                                                        key={d}
                                                        onClick={() => setDifficulty(d)}
                                                        className={`py-4 rounded-3xl font-black text-[10px] uppercase tracking-widest italic transition-all border ${
                                                            difficulty === d ? 'bg-zinc-900 text-white border-zinc-900' : 'bg-gray-50 text-gray-400 border-gray-100 hover:bg-white hover:border-primary/20'
                                                        }`}
                                                    >
                                                        {d}
                                                    </button>
                                                ))}
                                            </div>
                                        </section>

                                        <section className="space-y-4">
                                            <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                                <BrainCircuit className="w-3 h-3 text-primary" />
                                                <span>Intelligence Focus Matrix</span>
                                            </label>
                                            <div className="grid grid-cols-2 gap-3">
                                                {FOCUS_OPTIONS.map(area => {
                                                    const active = focusAreas.includes(area);
                                                    return (
                                                        <button
                                                            key={area}
                                                            onClick={() => toggleFocus(area)}
                                                            className={`p-4 rounded-3xl flex items-center justify-between group border transition-all ${
                                                                active ? 'bg-primary/5 border-primary/20 text-primary' : 'bg-gray-50 border-gray-100 text-gray-500 hover:bg-white'
                                                            }`}
                                                        >
                                                            <span className="text-[10px] font-black uppercase tracking-widest italic">{area}</span>
                                                            {active && <Check className="w-4 h-4" />}
                                                        </button>
                                                    );
                                                })}
                                            </div>
                                        </section>

                                        <button 
                                            onClick={handleInitialize}
                                            disabled={focusAreas.length === 0}
                                            className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-[0.3em] italic hover:bg-primary transition-all shadow-2xl flex items-center justify-center space-x-3 group"
                                        >
                                            <Rocket className="w-4 h-4 group-hover:-translate-y-1 transition-transform" />
                                            <span>Initialize Simulation</span>
                                        </button>
                                    </motion.div>
                                )}
                            </div>
                        )}
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
