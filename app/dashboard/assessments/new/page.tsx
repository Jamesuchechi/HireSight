"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, Plus, Trash2, Save, 
    Clock, Target, Layers, BrainCircuit,
    CheckCircle2, XCircle, HelpCircle, AlertCircle
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

interface Question {
    id: string;
    text: string;
    type: "mcq" | "checkbox";
    options: string[];
    correctAnswer: string;
    explanation: string;
    points: number;
}

export default function AssessmentArchitect() {
    const supabase = createClient();
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [jobs, setJobs] = useState<any[]>([]);
    
    // Form State
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [duration, setDuration] = useState(30);
    const [category, setCategory] = useState("technical");
    const [selectedJob, setSelectedJob] = useState("");
    const [customSkill, setCustomSkill] = useState("");
    const [questions, setQuestions] = useState<Question[]>([
        { id: "1", text: "", type: "mcq", options: ["", "", "", ""], correctAnswer: "0", explanation: "", points: 1 }
    ]);

    useEffect(() => {
        const fetchJobs = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;
            const { data } = await supabase.from("jobs").select("id, title, description").eq("company_id", user.id).neq("status", "deleted");
            if (data) setJobs(data);
        };
        fetchJobs();
    }, [supabase]);

    const addQuestion = () => {
        const newQuestion: Question = {
            id: Date.now().toString(),
            text: "",
            type: "mcq",
            options: ["", "", "", ""],
            correctAnswer: "0",
            explanation: "",
            points: 1
        };
        setQuestions([...questions, newQuestion]);
    };

    const removeQuestion = (id: string) => {
        if (questions.length === 1) return;
        setQuestions(questions.filter(q => q.id !== id));
    };

    const updateQuestion = (id: string, updates: Partial<Question>) => {
        setQuestions(questions.map(q => q.id === id ? { ...q, ...updates } : q));
    };

    const generateAIQuestions = async () => {
        if (!selectedJob && !customSkill) {
            alert("Please select a target mission (job) or enter a custom skill for the AI to analyze.");
            return;
        }

        setIsGenerating(true);
        try {
            const job = selectedJob ? jobs.find(j => j.id === selectedJob) : null;
            
            const response = await fetch("/api/assessments/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    jobTitle: job?.title, 
                    jobDescription: job?.description,
                    skill: customSkill
                })
            });

            if (!response.ok) throw new Error("AI Generation Failed");
            const data = await response.json();

            if (data.questions) {
                const formattedQuestions = data.questions.map((q: any, idx: number) => ({
                    id: (Date.now() + idx).toString(),
                    text: q.text,
                    type: q.type || "mcq",
                    options: q.options,
                    correctAnswer: q.correctAnswer.toString(),
                    explanation: q.explanation || "",
                    points: q.points || 1
                }));
                setQuestions(formattedQuestions);
            }
        } catch (error: any) {
            alert(`Neural Sync Error: ${error.message}`);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        if (!title || questions.some(q => !q.text)) {
            alert("Please complete the neural blueprint (Title and all Questions).");
            return;
        }

        setLoading(true);
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // 1. Create Assessment
            const { data: assessment, error: aError } = await supabase
                .from("assessments")
                .insert({
                    creator_id: user.id,
                    job_id: selectedJob || null,
                    title,
                    description,
                    duration_minutes: duration,
                    category
                })
                .select()
                .single();

            if (aError) throw aError;

            // 2. Create Questions
            const questionData = questions.map((q, idx) => ({
                assessment_id: assessment.id,
                question_text: q.text,
                question_type: q.type,
                options: q.options,
                correct_answer: q.correctAnswer,
                explanation: q.explanation,
                points: q.points,
                order_index: idx
            }));

            const { error: qError } = await supabase.from("assessment_questions").insert(questionData);
            if (qError) throw qError;

            router.push("/dashboard/screening");

        } catch (error: any) {
            console.error("Architect Failed:", error);
            alert(`Deployment Error: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-12 pb-32">
            {/* Header */}
            <header className="flex flex-col space-y-8">
                <Link 
                    href="/dashboard/screening" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Neural Base</span>
                </Link>

                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3">
                             <div className="p-3 bg-primary/10 text-primary rounded-2xl">
                                 <BrainCircuit className="w-6 h-6" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic">Assessment Architect</span>
                        </div>
                        <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                            Vetting <span className="text-primary tracking-normal">Blueprint</span>
                        </h1>
                        <p className="text-gray-500 font-bold max-w-lg">Design the technical gauntlet. Define the parameters of your neural assessment.</p>
                    </div>

                    <button 
                        onClick={handleSave}
                        disabled={loading}
                        className="px-10 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-105 transition-all flex items-center space-x-3 disabled:opacity-50"
                    >
                        <Save className="w-4 h-4" />
                        <span>{loading ? "Deploying..." : "Finalize Blueprint"}</span>
                    </button>
                </div>
            </header>

            {/* Core Blueprint Settings */}
            <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-8">
                    <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                        <div className="space-y-4">
                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest italic ml-4">Assessment Title</label>
                            <input 
                                type="text"
                                placeholder="e.g. Senior Logic Protocol v2.1"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                className="w-full px-8 py-6 bg-gray-50 border-none rounded-[28px] text-xl font-black italic focus:ring-4 focus:ring-primary/5 transition-all outline-none"
                            />
                        </div>
                        <div className="space-y-4">
                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest italic ml-4">Narrative Description</label>
                            <textarea 
                                rows={3}
                                placeholder="Describe the scope of this vetting protocol..."
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-8 py-6 bg-gray-50 border-none rounded-[28px] text-sm font-bold focus:ring-4 focus:ring-primary/5 transition-all outline-none resize-none"
                            />
                        </div>
                    </div>

                    {/* Mission vs Skill Targets */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="bg-white border border-gray-100 rounded-[40px] p-8 space-y-4 shadow-sm">
                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest italic flex items-center space-x-2">
                                <Target className="w-3 h-3 text-primary" />
                                <span>Target Mission (Optional)</span>
                            </label>
                            <select 
                                value={selectedJob}
                                onChange={(e) => setSelectedJob(e.target.value)}
                                className="w-full p-4 bg-gray-50 border-none rounded-2xl text-xs font-bold italic focus:ring-4 focus:ring-primary/5 transition-all outline-none"
                            >
                                <option value="">Select a job for context...</option>
                                {jobs.map(job => (
                                    <option key={job.id} value={job.id}>{job.title}</option>
                                ))}
                            </select>
                        </div>
                        <div className="bg-white border border-gray-100 rounded-[40px] p-8 space-y-4 shadow-sm">
                            <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest italic flex items-center space-x-2">
                                <BrainCircuit className="w-3 h-3 text-primary" />
                                <span>Or Draft by Skill</span>
                            </label>
                            <input 
                                type="text" 
                                placeholder="e.g. React, PostgreSQL..."
                                value={customSkill}
                                onChange={(e) => setCustomSkill(e.target.value)}
                                className="w-full p-4 bg-gray-50 border-none rounded-2xl text-xs font-bold italic focus:ring-4 focus:ring-primary/5 transition-all outline-none"
                            />
                        </div>
                    </div>
                </div>

                <div className="bg-zinc-900 rounded-[48px] p-10 shadow-2xl space-y-8 relative overflow-hidden group h-fit">
                     <div className="relative z-10 space-y-6">
                        <div className="flex items-center space-x-3 text-primary">
                             <Clock className="w-5 h-5" />
                             <h4 className="text-[10px] font-black uppercase tracking-widest italic">Runtime Constraints</h4>
                        </div>
                        <div className="space-y-4">
                             <div className="flex justify-between items-center text-white">
                                 <span className="text-xs font-bold italic">Duration (mins)</span>
                                 <input 
                                    type="number"
                                    value={duration}
                                    onChange={(e) => setDuration(parseInt(e.target.value))}
                                    className="w-20 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-center font-black text-primary italic focus:outline-none focus:border-primary transition-colors"
                                 />
                             </div>
                             <div className="flex justify-between items-center text-white">
                                 <span className="text-xs font-bold italic">Passed Index</span>
                                 <div className="px-3 py-2 bg-white/5 rounded-xl text-primary font-black italic text-xs">70%</div>
                             </div>
                        </div>
                     </div>
                     <div className="absolute right-0 bottom-0 w-48 h-48 bg-primary/20 blur-[80px] rounded-full translate-x-1/3 translate-y-1/3" />
                </div>
            </section>

            {/* Questions Sequence */}
            <div className="space-y-8">
                <div className="flex items-center justify-between px-4">
                     <div className="space-y-1">
                        <h2 className="text-2xl font-black text-zinc-900 italic tracking-tight">Question Sequence</h2>
                        <p className="text-[10px] font-bold text-gray-400 italic">Define the inquiry nodes for your vetting protocol.</p>
                     </div>
                     <div className="flex items-center space-x-4">
                        <button 
                            onClick={generateAIQuestions}
                            disabled={isGenerating || (!selectedJob && !customSkill)}
                            className="px-6 py-4 bg-primary text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic flex items-center space-x-2 hover:scale-105 transition-all shadow-xl shadow-primary/20 disabled:opacity-50 disabled:grayscale"
                        >
                            <BrainCircuit className={`w-4 h-4 ${isGenerating ? "animate-pulse" : ""}`} />
                            <span>{isGenerating ? "Neural Drafting..." : "Neural Draft (AI)"}</span>
                        </button>
                        <button 
                            onClick={addQuestion}
                            className="p-4 bg-white border border-gray-100 text-zinc-900 rounded-2xl hover:bg-zinc-900 hover:text-white transition-all shadow-sm"
                        >
                            <Plus className="w-6 h-6" />
                        </button>
                     </div>
                </div>

                <div className="space-y-6">
                    {questions.map((q, qIndex) => (
                        <motion.div 
                            key={q.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm relative group overflow-hidden"
                        >
                            <div className="absolute top-0 right-0 p-6 flex space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button 
                                    onClick={() => removeQuestion(q.id)}
                                    className="p-3 bg-red-50 text-red-500 rounded-xl hover:bg-red-500 hover:text-white transition-all"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                                <div className="lg:col-span-1">
                                    <div className="w-12 h-12 bg-gray-50 border border-gray-100 rounded-2xl flex items-center justify-center font-black text-primary italic">
                                        {qIndex + 1}
                                    </div>
                                </div>

                                <div className="lg:col-span-11 space-y-8">
                                    <input 
                                        type="text"
                                        placeholder="Neural Inquiry - What is the primary constraint of...?"
                                        value={q.text}
                                        onChange={(e) => updateQuestion(q.id, { text: e.target.value })}
                                        className="w-full px-8 py-6 bg-gray-50 border-none rounded-[24px] text-lg font-black italic focus:ring-4 focus:ring-primary/5 transition-all outline-none"
                                    />

                                    {/* Options Matrix */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {q.options.map((opt, oIndex) => (
                                            <div key={oIndex} className="relative group">
                                                <input 
                                                    type="text"
                                                    placeholder={`Option ${oIndex + 1}`}
                                                    value={opt}
                                                    onChange={(e) => {
                                                        const newOpts = [...q.options];
                                                        newOpts[oIndex] = e.target.value;
                                                        updateQuestion(q.id, { options: newOpts });
                                                    }}
                                                    className={`w-full pl-14 pr-6 py-4 bg-white border rounded-[20px] text-xs font-bold transition-all outline-none ${
                                                        q.correctAnswer === oIndex.toString() 
                                                        ? "border-emerald-500 ring-4 ring-emerald-500/5 bg-emerald-50/10" 
                                                        : "border-gray-100 hover:border-primary/20"
                                                    }`}
                                                />
                                                <button 
                                                    onClick={() => updateQuestion(q.id, { correctAnswer: oIndex.toString() })}
                                                    className={`absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                                                        q.correctAnswer === oIndex.toString()
                                                        ? "bg-emerald-500 border-emerald-500 text-white"
                                                        : "bg-white border-gray-200 text-transparent"
                                                    }`}
                                                >
                                                    <CheckCircle2 className="w-4 h-4" />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>

                <div className="flex justify-center pt-8">
                     <button 
                        onClick={addQuestion}
                        className="px-8 py-4 bg-white border-2 border-dashed border-gray-200 rounded-[28px] font-black text-[10px] uppercase tracking-widest text-gray-400 hover:border-primary/20 hover:text-primary transition-all flex items-center space-x-2"
                     >
                         <Plus className="w-4 h-4" />
                         <span>Add Query Node</span>
                     </button>
                </div>
            </div>
        </div>
    );
}
