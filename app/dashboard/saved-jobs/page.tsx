"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Database } from "@/types/database";
import CandidateJobCard from "@/components/jobs/CandidateJobCard";
import { Star, Search, Sparkles, Briefcase, Zap } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";

type SavedJob = {
    id: string;
    job_id: string;
    jobs: any;
};

export default function SavedJobsPage() {
    const supabase = createClient();
    const [savedJobs, setSavedJobs] = useState<SavedJob[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSavedJobs = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data, error } = await supabase
                .from("saved_jobs")
                .select(`
                    id,
                    job_id,
                    jobs (*, profiles:profiles!company_id(full_name, avatar_url))
                `)
                .eq("user_id", user.id);

            if (!error && data) {
                setSavedJobs(data as any);
            }
            setLoading(false);
        };

        fetchSavedJobs();
    }, [supabase]);

    const handleRemove = async (jobId: string) => {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { error } = await supabase
            .from("saved_jobs")
            .delete()
            .eq("user_id", user.id)
            .eq("job_id", jobId);

        if (!error) {
            setSavedJobs(prev => prev.filter(sj => sj.job_id !== jobId));
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
            <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between space-y-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 mb-2 italic tracking-tighter">
                        Archived <span className="text-primary tracking-normal">Opportunities</span>
                    </h1>
                    <p className="text-gray-500 font-bold">You have <span className="text-primary italic font-black">{savedJobs.length} positions</span> currently cached for later review.</p>
                </div>
            </header>

            {/* Quick Stats Banner */}
            <div className="bg-zinc-900 rounded-[40px] p-8 flex items-center justify-between border border-white/5">
                <div className="flex items-center space-x-6">
                    <div className="p-4 bg-primary rounded-[20px] shadow-xl shadow-primary/20">
                        <Star className="w-6 h-6 text-white fill-white" />
                    </div>
                    <div>
                        <h4 className="text-xl font-black text-white italic tracking-tight uppercase">Saved Protocol Store</h4>
                        <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest italic mt-1 font-body">Identity matrix analysis ready for deployment</p>
                    </div>
                </div>
                <div className="hidden md:flex items-center space-x-12 px-10 border-l border-white/10">
                     <div className="text-center">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Total Cache</p>
                        <p className="text-2xl font-black text-white italic">{savedJobs.length}</p>
                     </div>
                      <div className="text-center">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Expires Soon</p>
                        <p className="text-2xl font-black text-secondary italic">02</p>
                     </div>
                </div>
            </div>

            {/* Jobs Grid */}
            {savedJobs.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    <AnimatePresence>
                        {savedJobs.map((sj) => (
                            <motion.div
                                key={sj.id}
                                layout
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                            >
                                <CandidateJobCard 
                                    job={sj.jobs} 
                                    isSaved={true}
                                    onSave={() => handleRemove(sj.job_id)}
                                />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            ) : (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[48px] p-24 text-center space-y-6">
                    <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto">
                        <Star className="w-12 h-12 text-gray-200" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight">Persistence Matrix Empty</h3>
                        <p className="text-gray-500 font-bold max-w-sm mx-auto">
                            You haven't saved any positions yet. Start discovering amazing opportunities.
                        </p>
                    </div>
                    <Link 
                        href="/jobs"
                        className="inline-flex items-center space-x-3 px-10 py-5 bg-primary text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all"
                    >
                        <span>Initiate Discovery</span>
                        <Zap className="w-4 h-4" />
                    </Link>
                </div>
            )}
        </div>
    );
}
