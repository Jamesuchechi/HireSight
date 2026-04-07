"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Plus, BrainCircuit, Target, 
    Users, Clock, ArrowUpRight,
    TrendingUp, ShieldCheck, 
    ChevronRight, MoreHorizontal,
    Search, Filter
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function AssessmentMatrix() {
    const supabase = createClient();
    const [assessments, setAssessments] = useState<any[]>([]);
    const [stats, setStats] = useState({ total: 0, active: 0, candidates: 0 });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Fetch assessments with candidate attempt counts
            const { data: aData } = await supabase
                .from("assessments")
                .select(`
                    *,
                    attempts:assessment_attempts(count)
                `)
                .eq("creator_id", user.id)
                .order("created_at", { ascending: false });

            if (aData) {
                setAssessments(aData);
                const totalCandidates = aData.reduce((acc, curr) => acc + (curr.attempts?.[0]?.count || 0), 0);
                setStats({
                    total: aData.length,
                    active: aData.filter(a => a.is_active).length,
                    candidates: totalCandidates
                });
            }
            setLoading(false);
        };

        fetchData();
    }, [supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-32">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                <div className="space-y-4">
                    <div className="flex items-center space-x-3 text-primary">
                         <ShieldCheck className="w-6 h-6" />
                         <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">Vetting Intelligence</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter uppercase">
                        Assessment <span className="text-primary tracking-normal">Matrix</span>
                    </h1>
                    <p className="text-gray-500 font-bold max-w-lg">Architect and monitor technical vetting protocols for high-fidelity candidate matching.</p>
                </div>

                <Link 
                    href="/dashboard/assessments/new"
                    className="flex items-center space-x-3 px-8 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic hover:scale-105 transition-all shadow-2xl shadow-zinc-900/10"
                >
                    <Plus className="w-4 h-4" />
                    <span>Neural Architect</span>
                </Link>
            </header>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: "Neural Blueprints", value: stats.total, sub: `${stats.active} Active Nodes`, icon: <BrainCircuit className="w-6 h-6" /> },
                    { label: "Total Candidates", value: stats.candidates, sub: "Vetted across all missions", icon: <Users className="w-6 h-6" /> },
                    { label: "Avg. Passing Rate", value: "72%", sub: "Above standard baseline", icon: <TrendingUp className="w-6 h-6" /> }
                ].map((stat, i) => (
                    <div key={i} className="bg-white border border-gray-100 rounded-[40px] p-8 space-y-4 shadow-sm group hover:border-primary/20 transition-all">
                        <div className="flex items-center justify-between">
                            <div className="p-4 bg-primary/5 text-primary rounded-[24px] group-hover:bg-primary group-hover:text-white transition-all">
                                {stat.icon}
                            </div>
                            <ArrowUpRight className="w-5 h-5 text-gray-300" />
                        </div>
                        <div>
                            <h3 className="text-4xl font-black text-zinc-900 italic tracking-tighter">{stat.value}</h3>
                            <div className="flex items-center justify-between mt-1">
                                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{stat.label}</p>
                                <p className="text-[10px] font-bold text-primary italic uppercase">{stat.sub}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Assessment List */}
            <div className="space-y-6">
                <div className="flex items-center justify-between px-4">
                     <h2 className="text-2xl font-black text-zinc-900 italic tracking-tight">Active Protocols</h2>
                     <div className="flex items-center space-x-4">
                        <div className="bg-white border border-gray-100 rounded-2xl px-4 py-2 flex items-center space-x-3">
                             <Search className="w-4 h-4 text-gray-400" />
                             <input type="text" placeholder="Filter nodes..." className="bg-transparent border-none outline-none text-[10px] font-bold uppercase tracking-widest w-32" />
                        </div>
                     </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {assessments.map((a) => (
                        <div 
                            key={a.id}
                            className="bg-zinc-900 rounded-[40px] p-10 flex flex-col md:flex-row md:items-center justify-between gap-8 group hover:bg-zinc-800 transition-all relative overflow-hidden"
                        >
                            <div className="flex items-center space-x-8 relative z-10">
                                <div className="w-16 h-16 bg-white/10 rounded-[28px] flex items-center justify-center font-black text-white italic text-xl border border-white/5">
                                    {a.title[0]}
                                </div>
                                <div>
                                    <h4 className="text-2xl font-black text-white italic tracking-tight group-hover:text-primary transition-colors">{a.title}</h4>
                                    <div className="flex items-center space-x-4 mt-2">
                                        <span className="text-[10px] font-black text-white/40 uppercase tracking-widest flex items-center space-x-1">
                                            <Clock className="w-3 h-3 mr-1" />
                                            {a.duration_minutes}m Duration
                                        </span>
                                        <span className="text-[10px] font-black text-white/40 uppercase tracking-widest flex items-center space-x-1">
                                            <Target className="w-3 h-3 mr-1" />
                                            {a.passing_score}% Passing
                                        </span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center space-x-12 relative z-10">
                                <div className="hidden lg:block text-right">
                                    <p className="text-3xl font-black text-white italic tracking-tighter leading-none">{a.attempts?.[0]?.count || 0}</p>
                                    <p className="text-[8px] font-black text-white/40 uppercase tracking-[0.2em] mt-2">Neural Attempts</p>
                                </div>
                                <div className="flex items-center space-x-4">
                                     <button className="px-6 py-3 bg-white/5 text-white/60 rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-white/10 hover:text-white transition-all">
                                         Edit Model
                                     </button>
                                     <button className="p-3 bg-primary text-white rounded-2xl hover:scale-105 transition-all shadow-xl shadow-primary/20">
                                         <ChevronRight className="w-5 h-5" />
                                     </button>
                                </div>
                            </div>

                            {/* Background Aesthetic */}
                            <div className="absolute right-0 top-0 w-64 h-full bg-primary/5 -skew-x-12 translate-x-20 pointer-events-none" />
                        </div>
                    ))}
                    
                    {assessments.length === 0 && (
                        <div className="bg-white border-2 border-dashed border-gray-100 rounded-[56px] p-32 text-center space-y-8">
                             <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-300">
                                 <Plus className="w-12 h-12" />
                             </div>
                             <div className="space-y-4">
                                 <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight uppercase">No Blueprints Initialized</h3>
                                 <p className="text-gray-500 font-bold max-w-sm mx-auto italic">Deploy your first technical vetting protocol to start indexing candidate technical scores.</p>
                                 <Link 
                                    href="/dashboard/assessments/new"
                                    className="inline-flex px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-widest italic hover:scale-105 transition-all shadow-2xl"
                                 >
                                    Initialize Architect
                                 </Link>
                             </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
