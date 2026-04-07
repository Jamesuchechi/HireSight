"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Upload, X, CheckCircle2, 
    ArrowRight, Rocket, SlidersHorizontal, 
    BrainCircuit, Target, Zap, FileText,
    ChevronLeft, Loader2
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

export default function NewScreeningPage() {
    const supabase = createClient();
    const router = useRouter();
    const [jobs, setJobs] = useState<any[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [title, setTitle] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [progress, setProgress] = useState(0);

    const [weights, setWeights] = useState({
        skills: 40,
        experience: 30,
        education: 20,
        keywords: 10
    });

    const [criteria, setCriteria] = useState({
        requiredSkills: "",
        niceToHaveSkills: "",
        minExperience: 0,
        educationLevel: "Bachelor's",
        keywords: ""
    });

    useEffect(() => {
        const fetchJobs = async () => {
            const { data } = await supabase.from("jobs").select("id, title").eq("status", "active");
            if (data) setJobs(data);
        };
        fetchJobs();
    }, [supabase]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files).filter(f => f.type === "application/pdf");
            setFiles(prev => [...prev, ...newFiles].slice(0, 50));
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const startScreening = async () => {
        if (!title || files.length === 0) return;
        setUploading(true);

        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // 1. Upload files to Storage
            const fileData: { name: string, url: string }[] = [];
            for (const file of files) {
                const filePath = `${user.id}/${Date.now()}-${file.name}`;
                const { data: uploadData, error: uploadError } = await supabase.storage
                    .from("screening-resumes")
                    .upload(filePath, file);
                
                if (uploadError) throw uploadError;

                const { data: { publicUrl } } = supabase.storage
                    .from("screening-resumes")
                    .getPublicUrl(filePath);
                
                fileData.push({ name: file.name, url: publicUrl });
            }

            // 2. Create Screening Session
            const sessionResponse = await fetch("/api/screening/create", {
                method: "POST",
                body: JSON.stringify({
                    title,
                    jobId: selectedJob || null,
                    totalFiles: files.length,
                    criteria: {
                        requiredSkills: criteria.requiredSkills.split(",").map(s => s.trim()).filter(Boolean),
                        niceToHaveSkills: criteria.niceToHaveSkills.split(",").map(s => s.trim()).filter(Boolean),
                        minExperience: criteria.minExperience,
                        educationLevel: criteria.educationLevel,
                        keywords: criteria.keywords.split(",").map(s => s.trim()).filter(Boolean),
                        weights
                    }
                })
            });

            const session = await sessionResponse.json();
            if (session.error) throw new Error(session.error);

            // 3. Begin Processing (Client-Side Orchestrator to avoid timeouts)
            setUploading(false);
            setProcessing(true);
            
            let completedCount = 0;
            // Process in small batches of 3 to avoid AI rate limits but stay fast
            const batchSize = 3;
            for (let i = 0; i < fileData.length; i += batchSize) {
                const batch = fileData.slice(i, i + batchSize);
                await Promise.all(batch.map(async (file) => {
                    try {
                        const res = await fetch("/api/screening/process", {
                            method: "POST",
                            body: JSON.stringify({
                                sessionId: session.id,
                                resumeUrl: file.url
                            })
                        });
                        const data = await res.json();
                        if (data.error) console.error(`Error processing ${file.name}:`, data.error);
                    } catch (err) {
                        console.error(`Network error for ${file.name}:`, err);
                    } finally {
                        completedCount++;
                        setProgress(Math.round((completedCount / files.length) * 100));
                    }
                }));
            }

            // 4. Redirect on completion
            router.push(`/dashboard/screening/${session.id}`);

        } catch (error: any) {
            console.error("Screening Failed:", error);
            alert(`Failed: ${error.message}`);
            setUploading(false);
            setProcessing(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-24">
             {/* Header */}
             <header className="flex flex-col space-y-8">
                <Link 
                    href="/dashboard/screening" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-secondary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Cycle History</span>
                </Link>

                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3 text-secondary">
                             <BrainCircuit className="w-8 h-8" />
                             <span className="text-sm font-black uppercase tracking-widest italic decoration-2 underline decoration-secondary/20">Metric Extraction Engine</span>
                        </div>
                        <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                            New Neural <span className="text-secondary tracking-normal">Cycle</span>
                        </h1>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                 {/* Left Panel: Upload & Config */}
                 <div className="lg:col-span-2 space-y-10">
                     {/* Metadata Card */}
                     <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                         <div className="space-y-4">
                            <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Cycle Identity</h4>
                            <input 
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Quantum Research Team Vetting - Q1"
                                className="w-full text-3xl font-black italic text-zinc-900 placeholder:text-gray-100 focus:outline-none focus:placeholder:text-gray-50 transition-all border-b border-gray-50 pb-4"
                            />
                         </div>

                         <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                             <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Target Mission (Optional)</h4>
                                <select 
                                    value={selectedJob}
                                    onChange={(e) => setSelectedJob(e.target.value)}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl p-4 text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                >
                                    <option value="">Cold Pool (No Job Reference)</option>
                                    {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
                                </select>
                             </div>
                             <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Education Constraints</h4>
                                <select 
                                    value={criteria.educationLevel}
                                    onChange={(e) => setCriteria({ ...criteria, educationLevel: e.target.value })}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl p-4 text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                >
                                    <option>High School</option>
                                    <option>Bachelor's</option>
                                    <option>Master's</option>
                                    <option>PhD</option>
                                </select>
                             </div>
                         </div>
                     </section>

                     {/* Bulk Resume Matrix Dropzone */}
                     <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10">
                        <div className="flex items-center justify-between">
                             <h3 className="text-xl font-black text-zinc-900 italic uppercase">Resume Reservoir</h3>
                             <span className="text-[10px] font-black text-secondary italic uppercase tracking-widest">{files.length}/50 Metrics</span>
                        </div>

                        <div className="relative group">
                            <input 
                                type="file" 
                                multiple 
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                            />
                            <div className="border-4 border-dashed border-gray-100 rounded-[40px] p-16 flex flex-col items-center justify-center text-center space-y-6 group-hover:border-secondary/20 group-hover:bg-gray-50/50 transition-all">
                                <div className="p-6 bg-gray-50 rounded-full text-gray-300 group-hover:bg-white group-hover:text-secondary group-hover:scale-110 transition-all shadow-sm">
                                    <Upload className="w-10 h-10" />
                                </div>
                                <div>
                                    <h4 className="text-xl font-black text-zinc-900 italic tracking-tight">Extract Raw Metrics</h4>
                                    <p className="text-xs text-gray-400 font-bold max-w-sm italic">Drag up to 50 PDF files directly into the neural cloud for vetting.</p>
                                </div>
                            </div>
                        </div>

                        {files.length > 0 && (
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                <AnimatePresence>
                                    {files.map((file, i) => (
                                        <motion.div 
                                            key={`${file.name}-${i}`}
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            className="bg-gray-50 border border-gray-100 rounded-2xl p-4 flex items-center justify-between group"
                                        >
                                            <div className="flex items-center space-x-3 overflow-hidden">
                                                <div className="p-2 bg-white rounded-lg text-gray-400">
                                                    <FileText className="w-4 h-4" />
                                                </div>
                                                <span className="text-[10px] font-black text-zinc-900 truncate italic">{file.name}</span>
                                            </div>
                                            <button onClick={() => removeFile(i)} className="p-1 hover:text-red-500 transition-colors">
                                                <X className="w-4 h-4" />
                                            </button>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                            </div>
                        )}
                     </section>

                     {/* Criteria Config */}
                     <section className="bg-zinc-900 rounded-[48px] p-12 shadow-2xl space-y-10">
                        <div className="flex items-center space-x-3">
                            <Target className="w-6 h-6 text-secondary" />
                            <h3 className="text-2xl font-black text-white italic tracking-tight uppercase">Target Constraints</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Critical Skills</h5>
                                    <textarea 
                                        rows={3}
                                        value={criteria.requiredSkills}
                                        onChange={(e) => setCriteria({...criteria, requiredSkills: e.target.value})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-sm font-bold italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                        placeholder="Comma separated: Python, React, AWS..."
                                    />
                                </div>
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Experience (Years)</h5>
                                    <input 
                                        type="number"
                                        value={criteria.minExperience}
                                        onChange={(e) => setCriteria({...criteria, minExperience: parseInt(e.target.value)})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-3xl font-black italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                    />
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Neural Keywords</h5>
                                    <textarea 
                                        rows={8}
                                        value={criteria.keywords}
                                        onChange={(e) => setCriteria({...criteria, keywords: e.target.value})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-sm font-bold italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                        placeholder="Keywords to boost matching: Startup, Scale-up, Leadership, High Performance..."
                                    />
                                </div>
                            </div>
                        </div>
                     </section>
                 </div>

                 {/* Right Panel: Weighting & Action */}
                 <div className="space-y-8">
                    <div className="sticky top-8 space-y-8">
                         {/* Weighted Scoring Controller */}
                         <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-xl space-y-10">
                            <div className="flex items-center space-x-3">
                                <SlidersHorizontal className="w-5 h-5 text-primary" />
                                <h3 className="text-xl font-black text-zinc-900 italic uppercase">Weighted Logic</h3>
                            </div>

                            <div className="space-y-8">
                                {[
                                    { key: "skills", label: "Skills Density", val: weights.skills, color: "accent-primary" },
                                    { key: "experience", label: "Experience Tenure", val: weights.experience, color: "accent-secondary" },
                                    { key: "education", label: "Academic Sync", val: weights.education, color: "accent-zinc-900" },
                                    { key: "keywords", label: "Keyword Hitrate", val: weights.keywords, color: "accent-emerald-500" }
                                ].map((w) => (
                                    <div key={w.key} className="space-y-3">
                                        <div className="flex justify-between items-center px-1">
                                            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">{w.label}</span>
                                            <span className="text-xs font-black text-zinc-900 italic">{w.val}%</span>
                                        </div>
                                        <input 
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={w.val}
                                            onChange={(e) => setWeights({ ...weights, [w.key]: parseInt(e.target.value) })}
                                            className={`w-full h-1.5 bg-gray-100 rounded-full appearance-none cursor-pointer ${w.color}`}
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="p-6 bg-gray-50 rounded-3xl space-y-2">
                                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic text-center">Neural Configuration Status</p>
                                <div className="text-center font-black italic text-xl">
                                    {Object.values(weights).reduce((a, b) => a + b, 0) === 100 ? (
                                        <span className="text-emerald-500">OPTIMAL (100%)</span>
                                    ) : (
                                        <span className="text-amber-500 text-sm italic">UNSTABLE ({Object.values(weights).reduce((a, b) => a + b, 0)}%)</span>
                                    )}
                                </div>
                            </div>
                         </section>

                         {/* Action Buttons */}
                         <div className="space-y-4">
                            <button 
                                onClick={startScreening}
                                disabled={uploading || processing || files.length === 0 || !title}
                                className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-lg uppercase tracking-widest italic shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale group relative overflow-hidden"
                            >
                                <div className="relative z-10 flex items-center justify-center space-x-3">
                                    {(uploading || processing) ? (
                                        <Loader2 className="w-6 h-6 animate-spin" />
                                    ) : (
                                        <Zap className="w-6 h-6 text-primary group-hover:scale-125 transition-transform" />
                                    )}
                                    <span>Initiate Vetting Cycle</span>
                                </div>
                                <div className="absolute inset-0 bg-primary/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-700" />
                            </button>

                            <button className="w-full py-5 border-2 border-gray-100 text-gray-400 rounded-[32px] font-black text-xs uppercase tracking-widest italic hover:bg-gray-50 transition-all">
                                Save Simulation Template
                            </button>
                         </div>
                    </div>
                 </div>
            </div>

            {/* Overlays */}
            <AnimatePresence>
                {(uploading || processing) && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-zinc-900/90 z-50 flex items-center justify-center p-6 backdrop-blur-xl"
                    >
                        <div className="max-w-md w-full space-y-12 text-center text-white">
                             <div className="relative">
                                 <motion.div 
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                    className="w-48 h-48 border-4 border-white/5 border-t-secondary rounded-full mx-auto"
                                 />
                                 <BrainCircuit className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 text-white animate-pulse" />
                             </div>

                             <div className="space-y-4">
                                <h3 className="text-4xl font-black italic tracking-tighter uppercase">
                                    {uploading ? "Deploying Metrics..." : "Computing Intelligence..."}
                                </h3>
                                <p className="text-gray-400 font-bold italic">
                                    {uploading ? "Transmitting files to neural cloud storage." : "AI is analyzing resume matrices against constraints."}
                                </p>
                             </div>

                             <div className="space-y-4">
                                 <div className="flex justify-between items-end text-[10px] font-black uppercase tracking-widest text-secondary">
                                     <span>Vector Progress</span>
                                     <span>{progress}%</span>
                                 </div>
                                 <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden border border-white/5">
                                     <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        className="h-full bg-secondary shadow-[0_0_20px_rgba(255,102,0,0.8)]"
                                     />
                                 </div>
                                 <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-gray-500">
                                     <span>Batch processing active</span>
                                     <span>Metric Stream {Math.ceil(progress * files.length / 100)} / {files.length}</span>
                                 </div>
                             </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
