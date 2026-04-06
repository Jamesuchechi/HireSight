"use client";

import { useState } from "react";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ResumeUploadProps {
    onSuccess?: (data: any) => void;
}

export default function ResumeUpload({ onSuccess }: ResumeUploadProps) {
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/api/ai/parse", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to parse resume.");
            }

            setResult(data);
            if (onSuccess) onSuccess(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="w-full">
            <div className="relative group">
                <input
                    type="file"
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    onChange={handleFileChange}
                    accept=".pdf,.txt"
                    disabled={uploading}
                />
                
                <div className={`
                    relative p-8 border-2 border-dashed rounded-[32px] transition-all duration-500
                    flex flex-col items-center justify-center text-center space-y-4
                    ${uploading ? "bg-gray-50 border-gray-200" : "bg-white border-gray-100 group-hover:border-primary/30 group-hover:bg-primary/5"}
                `}>
                    <div className={`
                        p-4 rounded-2xl transition-all duration-500
                        ${uploading ? "bg-gray-100 text-gray-400" : "bg-primary/10 text-primary group-hover:scale-110 group-hover:rotate-3"}
                    `}>
                        {uploading ? <Loader2 className="w-8 h-8 animate-spin" /> : <FileText className="w-8 h-8" />}
                    </div>

                    <div className="space-y-1">
                        <h4 className="text-lg font-black font-display text-zinc-900 italic uppercase">
                            {uploading ? "Analyzing Protocol..." : "Upload Professional Resume"}
                        </h4>
                        <p className="text-xs text-gray-400 font-bold uppercase tracking-widest">
                            PDF or TXT supported • AI Automated Parsing
                        </p>
                    </div>
                    
                    {/* Animated background decoration */}
                    {!uploading && (
                        <div className="absolute top-[-20px] right-[-20px] w-20 h-20 bg-primary/5 blur-3xl rounded-full group-hover:scale-150 transition-transform duration-700 pointer-events-none" />
                    )}
                </div>
            </div>

            {/* Status Messages */}
            <AnimatePresence>
                {error && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mt-4 p-4 bg-red-50 border border-red-100 rounded-2xl flex items-center space-x-3 text-red-600"
                    >
                        <AlertCircle className="w-5 h-5" />
                        <span className="text-xs font-black italic uppercase tracking-widest">{error}</span>
                    </motion.div>
                )}

                {result && !uploading && (
                    <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0 }}
                        className="mt-6 space-y-4"
                    >
                        <div className="p-6 bg-emerald-50 border border-emerald-100 rounded-[32px] flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <div className="p-3 bg-emerald-500 text-white rounded-xl">
                                    <CheckCircle2 className="w-5 h-5" />
                                </div>
                                <div>
                                    <p className="font-black text-emerald-900 italic leading-none">{result.fullName}</p>
                                    <p className="text-[10px] text-emerald-600 font-black uppercase tracking-widest mt-1">Structured Profile Synthesized</p>
                                </div>
                            </div>
                            <div className="px-4 py-2 bg-white rounded-xl border border-emerald-100 text-[10px] font-black text-emerald-600 uppercase tracking-[0.2em] shadow-sm">
                                AI VERIFIED
                            </div>
                        </div>
                        
                        {/* Compact Skills Display */}
                        <div className="flex flex-wrap gap-2">
                           {result.skills.hard.slice(0, 5).map((skill: string) => (
                               <span key={skill} className="px-3 py-1.5 bg-zinc-900 text-white text-[10px] font-black uppercase tracking-widest rounded-lg flex items-center space-x-2">
                                   <Sparkles className="w-3 h-3 text-primary" />
                                   <span>{skill}</span>
                               </span>
                           ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
