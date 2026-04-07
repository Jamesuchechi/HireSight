"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Users, Search, Filter, Mail, 
    MoreVertical, ArrowUpRight, 
    Star, MessageSquare, Briefcase,
    Zap, Trash2, MapPin
} from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function CandidatePoolPage() {
    const supabase = createClient();
    const [candidates, setCandidates] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        const fetchCandidatePool = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Logic: Fetch unique profiles that have applied to any of this recruiter's jobs
            const { data, error } = await supabase
                .from("job_applications")
                .select(`
                    candidate:profiles!candidate_id(*),
                    job:jobs(id, title),
                    created_at,
                    match_score
                `)
                .eq("job:jobs.company_id", user.id)
                .order("created_at", { ascending: false });

            if (data) {
                // Group by candidate ID to show unique pool members
                const uniquePool: any[] = [];
                const seenIds = new Set();

                data.forEach((app: any) => {
                    if (app.candidate && !seenIds.has(app.candidate.id)) {
                        uniquePool.push({
                            ...app.candidate,
                            lastApplied: app.created_at,
                            lastJob: app.job.title,
                            avgMatch: app.match_score || 85
                        });
                        seenIds.add(app.candidate.id);
                    }
                });
                setCandidates(uniquePool);
            }
            setLoading(false);
        };

        fetchCandidatePool();
    }, [supabase]);

    const filteredPool = candidates.filter(c => 
        c.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.bio?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div className="space-y-4">
                    <div className="flex items-center space-x-3">
                         <div className="p-3 bg-secondary/10 text-secondary rounded-[20px]">
                             <Users className="w-6 h-6" />
                         </div>
                         <span className="text-[10px] font-black text-secondary uppercase tracking-[0.2em] italic underline decoration-2 decoration-secondary/20">Talent Reservoir</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Candidate <span className="text-secondary tracking-normal">Pool</span>
                    </h1>
                    <p className="text-gray-500 font-bold max-w-lg">Manage your global talent matrix. These are all unit metrics that have engaged with your organization.</p>
                </div>

                <div className="flex items-center -space-x-3">
                    {candidates.slice(0, 5).map((c, i) => (
                        <div key={i} className="w-12 h-12 rounded-full border-4 border-white overflow-hidden bg-gray-100 shadow-xl ring-2 ring-gray-100">
                             {c.avatar_url ? <img src={c.avatar_url} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center font-black text-xs text-gray-400">{c.full_name[0]}</div>}
                        </div>
                    ))}
                    {candidates.length > 5 && (
                        <div className="w-12 h-12 rounded-full border-4 border-white bg-secondary text-white flex items-center justify-center text-[10px] font-black italic shadow-xl">
                            +{candidates.length - 5}
                        </div>
                    )}
                </div>
            </header>

            {/* Matrix Search & Filters */}
            <div className="flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 group">
                    <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-secondary transition-colors" />
                    <input 
                        type="text"
                        placeholder="Scan talent matrix for full name or bio keywords..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-16 pr-6 py-5 bg-white border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-secondary/5 transition-all shadow-sm"
                    />
                </div>
                <button className="px-8 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-widest italic flex items-center space-x-3 hover:scale-[1.03] transition-all">
                    <Filter className="w-4 h-4" />
                    <span>Global Filters</span>
                </button>
            </div>

            {/* Talent Matrix Grid */}
            {filteredPool.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {filteredPool.map((c) => (
                        <motion.div
                            key={c.id}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            className="bg-white border border-gray-100 rounded-[48px] p-8 hover:shadow-2xl hover:border-secondary/20 transition-all group relative overflow-hidden"
                        >
                            <div className="relative z-10 space-y-6">
                                <div className="flex items-start justify-between">
                                    <div className="w-20 h-20 bg-gray-50 rounded-[32px] border border-gray-100 flex items-center justify-center font-black text-secondary italic overflow-hidden shadow-lg ring-4 ring-white group-hover:scale-110 transition-transform">
                                        {c.avatar_url ? <img src={c.avatar_url} className="w-full h-full object-cover" /> : <span className="text-3xl">{c.full_name[0]}</span>}
                                    </div>
                                    <button className="p-3 hover:bg-gray-50 rounded-2xl transition-all">
                                        <Star className="w-5 h-5 text-gray-200 hover:text-amber-500 transition-colors" />
                                    </button>
                                </div>

                                <div>
                                    <h4 className="text-2xl font-black text-zinc-900 italic tracking-tight">{c.full_name}</h4>
                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 italic">Last Applied: {c.lastJob}</p>
                                </div>

                                <div className="space-y-4">
                                     <div className="flex items-center space-x-2 text-primary">
                                         <Zap className="w-4 h-4 animate-pulse" />
                                         <span className="text-xs font-black uppercase tracking-widest italic">Neural Match: {c.avgMatch}%</span>
                                     </div>
                                     <p className="text-xs text-gray-500 font-bold italic line-clamp-2 leading-relaxed">
                                         {c.bio || "No biography transmission detected."}
                                     </p>
                                </div>

                                <div className="pt-6 border-t border-gray-50 flex items-center justify-between">
                                    <div className="flex space-x-2">
                                         <button className="p-3 bg-gray-50 text-gray-400 hover:bg-secondary hover:text-white rounded-xl transition-all">
                                             <Mail className="w-4 h-4" />
                                         </button>
                                         <button className="p-3 bg-gray-50 text-gray-400 hover:bg-zinc-900 hover:text-white rounded-xl transition-all">
                                             <MessageSquare className="w-4 h-4" />
                                         </button>
                                    </div>
                                    <button 
                                        onClick={() => console.log("Extract Talent Profile", c.id)}
                                        className="text-[10px] font-black text-zinc-900 uppercase tracking-widest hover:text-secondary flex items-center space-x-2"
                                    >
                                        <span>Audit Profile</span>
                                        <ArrowUpRight className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                            <div className="absolute right-0 bottom-0 w-40 h-40 bg-secondary/5 blur-3xl rounded-full translate-x-1/2 translate-y-1/2" />
                        </motion.div>
                    ))}
                </div>
            ) : (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[48px] p-24 text-center space-y-6">
                     <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-200">
                         <Users className="w-12 h-12" />
                     </div>
                     <div>
                         <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight">Pool Matrix Empty</h3>
                         <p className="text-gray-500 font-bold max-w-sm mx-auto">No unique talent profiles have been successfully indexed for your organization yet.</p>
                     </div>
                </div>
            )}
        </div>
    );
}
