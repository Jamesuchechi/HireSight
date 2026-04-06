"use client";

import { useEffect, useState } from "react";
import { 
    FileText, 
    Plus, 
    Trash2, 
    CheckCircle2, 
    Clock, 
    AlertCircle, 
    MoreVertical,
    Download,
    Eye,
    Star,
    Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ResumeUpload from "@/components/ResumeUpload";

interface Resume {
    id: string;
    title: string;
    file_url: string;
    status: 'uploaded' | 'parsing' | 'parsed' | 'failed';
    is_primary: boolean;
    created_at: string;
    parsed_content: any;
}

export default function ResumesPage() {
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [loading, setLoading] = useState(true);
    const [showUpload, setShowUpload] = useState(false);

    const fetchResumes = async () => {
        try {
            const response = await fetch("/api/resumes");
            const data = await response.json();
            if (response.ok) setResumes(data);
        } catch (error) {
            console.error("Failed to fetch resumes:", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchResumes();
    }, []);

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this resume?")) return;
        
        try {
            const response = await fetch("/api/resumes", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id })
            });

            if (response.ok) {
                setResumes(resumes.filter(r => r.id !== id));
            }
        } catch (error) {
            console.error("Delete failed:", error);
        }
    };

    const handleSetPrimary = async (id: string) => {
        try {
            const response = await fetch("/api/resumes", {
                method: "POST", // POST handles primary toggle logic in route
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    id, 
                    is_primary: true,
                    // We only need id/is_primary but the route expects a full insert if it doesn't exist
                    // This is a simplified primary toggle for now. 
                    // Better to have a dedicated /api/resumes/[id]/primary route, but for now we follow the API we built.
                })
            });
            // Simplified: Just re-fetch for now to ensure consistency
            fetchResumes();
        } catch (error) {
            console.error("Set primary failed:", error);
        }
    };

    const handleUploadSuccess = async (parsedData: any) => {
        // After AI parsing succeeds, save metadata to DB
        // The file_url handling would normally be done during upload. 
        // For this demo, we'll assume the ResumeUpload component returns a file path or URL.
        // Since ResumeUpload currently just returns the parsed AI data, we'll use that.
        
        try {
            const response = await fetch("/api/resumes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: `Resume ${new Date().toLocaleDateString()}`,
                    file_url: "pending_upload_ref", // In production, this comes from Supabase Storage
                    status: 'parsed',
                    parsed_content: parsedData,
                    is_primary: resumes.length === 0
                })
            });

            if (response.ok) {
                fetchResumes();
                setShowUpload(false);
            }
        } catch (error) {
            console.error("Save failed:", error);
        }
    };

    return (
        <div className="max-w-7xl mx-auto pb-20">
            {/* Header Area */}
            <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
                <div>
                    <h1 className="text-5xl font-black font-display text-zinc-900 italic uppercase tracking-tighter leading-none">
                        Resume Laboratory
                    </h1>
                    <p className="text-gray-400 font-bold uppercase tracking-[0.3em] text-[10px] mt-4 ml-1">
                        AI-Enabled Professional DNA Storage
                    </p>
                </div>
                <button 
                    onClick={() => setShowUpload(!showUpload)}
                    className="px-8 py-4 bg-zinc-900 text-white rounded-[24px] font-black italic flex items-center space-x-3 hover:scale-105 transition-all shadow-2xl active:scale-95"
                >
                    <Plus className="w-5 h-5" />
                    <span>SYNTHESIZE NEW</span>
                </button>
            </div>

            <AnimatePresence>
                {showUpload && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="mb-12 overflow-hidden"
                    >
                        <div className="p-8 bg-primary/5 border-2 border-dashed border-primary/20 rounded-[40px]">
                            <ResumeUpload onSuccess={handleUploadSuccess} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Resume Grid */}
            {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-64 bg-gray-100 rounded-[40px] animate-pulse" />
                    ))}
                </div>
            ) : resumes.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {resumes.map((resume) => (
                        <motion.div 
                            key={resume.id}
                            layout
                            className={`group relative bg-white border rounded-[40px] p-8 transition-all hover:shadow-2xl hover:-translate-y-2 overflow-hidden ${
                                resume.is_primary ? "border-primary ring-4 ring-primary/5" : "border-gray-100"
                            }`}
                        >
                            {/* Status Indicator */}
                            <div className="flex items-center justify-between mb-8">
                                <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest flex items-center space-x-2 ${
                                    resume.status === 'parsed' ? "bg-emerald-50 text-emerald-600" :
                                    resume.status === 'parsing' ? "bg-blue-50 text-blue-600" :
                                    "bg-gray-50 text-gray-500"
                                }`}>
                                    {resume.status === 'parsed' ? <CheckCircle2 className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                                    <span>{resume.status}</span>
                                </div>
                                {resume.is_primary && (
                                    <div className="flex items-center space-x-2 text-primary">
                                        <Star className="w-4 h-4 fill-primary" />
                                        <span className="text-[10px] font-black uppercase tracking-widest">Active</span>
                                    </div>
                                )}
                            </div>

                            {/* Resume Info */}
                            <div className="mb-10 text-center">
                                <div className="w-16 h-16 bg-gray-50 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform duration-500">
                                    <FileText className="w-8 h-8 text-zinc-900" />
                                </div>
                                <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase truncate">
                                    {resume.title}
                                </h3>
                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-2 leading-none">
                                    SYNTHESIZED {new Date(resume.created_at).toLocaleDateString()}
                                </p>
                            </div>

                            {/* Skills Snapshot */}
                            <div className="flex flex-wrap gap-1.5 justify-center mb-10">
                                {resume.parsed_content?.skills?.hard?.slice(0, 3).map((skill: string) => (
                                    <span key={skill} className="px-2.5 py-1 bg-gray-50 text-gray-500 text-[9px] font-black uppercase tracking-widest rounded-lg">
                                        {skill}
                                    </span>
                                ))}
                            </div>

                            {/* Actions */}
                            <div className="grid grid-cols-2 gap-3">
                                <button 
                                    onClick={() => handleSetPrimary(resume.id)}
                                    disabled={resume.is_primary}
                                    className={`py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                                        resume.is_primary 
                                        ? "bg-emerald-50 text-emerald-600 cursor-default" 
                                        : "bg-gray-50 text-gray-400 hover:bg-primary/10 hover:text-primary"
                                    }`}
                                >
                                    {resume.is_primary ? "ACTIVE" : "SET ACTIVE"}
                                </button>
                                <button 
                                    onClick={() => handleDelete(resume.id)}
                                    className="py-3 bg-gray-50 text-gray-400 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-red-50 hover:text-red-500 transition-all"
                                >
                                    PURGE
                                </button>
                            </div>

                            {/* Background Decoration */}
                            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                <Sparkles className="w-20 h-20" />
                            </div>
                        </motion.div>
                    ))}
                </div>
            ) : (
                <div className="flex flex-col items-center justify-center py-32 bg-white border border-dashed border-gray-100 rounded-[40px] text-center space-y-6">
                    <div className="p-8 bg-gray-50 rounded-full">
                        <FileText className="w-16 h-16 text-gray-200" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Your Library is Empty</h3>
                        <p className="text-gray-400 font-bold uppercase tracking-widest text-xs mt-2">Upload your first resume to activate AI synthesis</p>
                    </div>
                </div>
            )}
        </div>
    );
}
