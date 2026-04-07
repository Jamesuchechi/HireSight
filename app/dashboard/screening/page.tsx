"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Plus, Search, Filter, Rocket, 
    Layers, Clock, CheckCircle2, 
    XCircle, Users, BarChart2,
    ArrowRight, Zap
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";

export default function ScreeningHistoryPage() {
    const supabase = createClient();
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");

    useEffect(() => {
        const fetchSessions = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data, error } = await supabase
                .from("screening_sessions")
                .select(`
                    *,
                    job:jobs(title)
                `)
                .order("created_at", { ascending: false });

            if (data) setSessions(data);
            setLoading(false);
        };

        fetchSessions();

        // Subscribe to real-time updates for progress bars
        const channel = supabase
            .channel('screening_updates')
            .on('postgres_changes', { 
                event: 'UPDATE', 
                schema: 'public', 
                table: 'screening_sessions' 
            }, (payload) => {
                setSessions(prev => prev.map(s => s.id === payload.new.id ? { ...s, ...payload.new } : s));
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [supabase]);

    const filteredSessions = sessions.filter(s => 
        s.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.job?.title?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                <div className="space-y-4">
                    <div className="flex items-center space-x-3 text-secondary underline decoration-2 decoration-secondary/20">
                         <Layers className="w-6 h-6" />
                         <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">AI Neural Vetting</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Screening <span className="text-secondary tracking-normal">Cycles</span>
                    </h1>
                    <p className="text-gray-500 font-bold max-w-lg">Execute bulk metric analysis across your talent reservoirs with weighted intelligence.</p>
                </div>

                <Link
                    href="/dashboard/screening/new"
                    className="inline-flex items-center space-x-3 px-10 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-sm uppercase tracking-widest italic shadow-2xl hover:scale-[1.05] active:scale-[0.95] transition-all group"
                >
                    <Plus className="w-5 h-5 group-hover:rotate-90 transition-transform" />
                    <span>Initiate Cycle</span>
                </Link>
            </header>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                 {[
                    { label: "Total Files Vetted", val: sessions.reduce((acc, s) => acc + s.total_files, 0), icon: <Users className="w-5 h-5" />, color: "text-primary", bg: "bg-primary/10" },
                    { label: "Neural Success Rate", val: "94.2%", icon: <CheckCircle2 className="w-5 h-5" />, color: "text-emerald-500", bg: "bg-emerald-50" },
                    { label: "Compute Efficiency", val: "≈ 2.4s", icon: <Zap className="w-5 h-5" />, color: "text-amber-500", bg: "bg-amber-50" }
                 ].map((stat, i) => (
                    <div key={i} className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm flex items-center space-x-6">
                         <div className={`p-4 rounded-2xl ${stat.bg} ${stat.color}`}>
                             {stat.icon}
                         </div>
                         <div>
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">{stat.label}</p>
                            <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{stat.val}</h4>
                         </div>
                    </div>
                 ))}
            </div>

            {/* Sessions List */}
            <div className="space-y-6">
                <div className="flex flex-col md:flex-row gap-4 items-center">
                    <div className="relative flex-1 group">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-secondary transition-colors" />
                        <input 
                            type="text"
                            placeholder="Scan cycles for title or job reference..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-16 pr-6 py-5 bg-white border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-secondary/5 transition-all shadow-sm"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-6">
                    <AnimatePresence mode="popLayout">
                        {filteredSessions.map((s) => (
                            <motion.div
                                key={s.id}
                                layout
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="bg-white border border-gray-100 rounded-[48px] p-8 hover:shadow-xl transition-all group flex flex-col md:flex-row md:items-center justify-between gap-8 relative overflow-hidden"
                            >
                                <div className="flex items-center space-x-6 relative z-10">
                                     <div className={`w-16 h-16 rounded-[24px] flex items-center justify-center shadow-lg ${
                                         s.status === 'completed' ? "bg-emerald-50 text-emerald-500" :
                                         s.status === 'processing' ? "bg-primary/5 text-primary" :
                                         "bg-gray-50 text-gray-400"
                                     }`}>
                                         {s.status === 'processing' ? <Zap className="w-8 h-8 animate-pulse" /> : <Layers className="w-8 h-8" />}
                                     </div>
                                     <div className="space-y-1">
                                         <h3 className="text-xl font-black text-zinc-900 italic tracking-tight uppercase">{s.title}</h3>
                                         <p className="text-xs font-bold text-gray-500 italic max-w-xs truncate">Ref: {s.job?.title || "Manual Reservoir Upload"}</p>
                                     </div>
                                </div>

                                <div className="flex-1 max-w-md relative z-10">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Computing Matrix: {s.processed_count}/{s.total_files}</span>
                                        <span className="text-[10px] font-black text-secondary italic">{Math.round((s.processed_count / s.total_files) * 100)}%</span>
                                    </div>
                                    <div className="w-full h-2 bg-gray-50 rounded-full overflow-hidden">
                                        <motion.div 
                                            initial={{ width: 0 }}
                                            animate={{ width: `${(s.processed_count / s.total_files) * 100}%` }}
                                            className="h-full bg-secondary shadow-[0_0_10px_rgba(255,102,0,0.5)]"
                                        />
                                    </div>
                                </div>

                                <div className="flex items-center space-x-6 relative z-10">
                                    <div className="text-right flex flex-col items-end">
                                         <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1 italic">Cycle Start</span>
                                         <span className="text-sm font-black text-zinc-900 italic">{formatDistanceToNow(new Date(s.created_at))} ago</span>
                                    </div>
                                    <Link 
                                        href={`/dashboard/screening/${s.id}`}
                                        className="px-8 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic group-hover:bg-secondary transition-all flex items-center space-x-2"
                                    >
                                        <span>Audit Data</span>
                                        <ArrowRight className="w-4 h-4" />
                                    </Link>
                                </div>

                                <div className="absolute right-0 bottom-0 w-32 h-32 bg-secondary/5 blur-3xl rounded-full translate-x-1/2 translate-y-1/2 group-hover:bg-secondary/10 transition-colors" />
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    {sessions.length === 0 && !loading && (
                        <div className="bg-white border-2 border-dashed border-gray-100 rounded-[56px] p-32 text-center space-y-8">
                             <div className="w-32 h-32 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-200">
                                 <BarChart2 className="w-16 h-16" />
                             </div>
                             <div className="space-y-2">
                                 <h3 className="text-4xl font-black text-zinc-900 italic tracking-tighter">Zero Cycles Detected</h3>
                                 <p className="text-gray-500 font-bold max-w-md mx-auto italic">Your organization has not yet executed any AI neural vetting sessions across talent reservoirs.</p>
                             </div>
                             <Link href="/dashboard/screening/new" className="inline-flex px-12 py-5 bg-secondary text-white rounded-3xl font-black text-sm uppercase italic hover:scale-105 transition-all shadow-xl">
                                 Start First Cycle
                             </Link>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
