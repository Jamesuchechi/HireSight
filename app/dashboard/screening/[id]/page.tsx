"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ChevronLeft, BarChart3, Users, 
    Zap, Rocket, Star, Search, Filter,
    CheckCircle2, XCircle, Download,
    ArrowUpRight, PieChart, Info,
    MessageSquare, Briefcase, GraduationCap
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, 
    Tooltip, ResponsiveContainer, Cell,
    AreaChart, Area
} from "recharts";
import { formatDistanceToNow } from "date-fns";

export default function ScreeningResultsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const supabase = createClient();
    const [session, setSession] = useState<any>(null);
    const [results, setResults] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedResult, setSelectedResult] = useState<any>(null);

    useEffect(() => {
        const fetchResults = async () => {
            const { data: sessionData } = await supabase
                .from("screening_sessions")
                .select("*, job:jobs(title)")
                .eq("id", id)
                .single();
            
            const { data: resultData } = await supabase
                .from("screening_results")
                .select("*")
                .eq("session_id", id)
                .order("match_score", { ascending: false });

            if (sessionData) setSession(sessionData);
            if (resultData) setResults(resultData);
            setLoading(false);
        };

        fetchResults();

        // Real-time updates for processing sessions
        const channel = supabase
            .channel(`results_${id}`)
            .on('postgres_changes', { 
                event: 'INSERT', 
                schema: 'public', 
                table: 'screening_results',
                filter: `session_id=eq.${id}`
            }, (payload) => {
                setResults(prev => [payload.new, ...prev].sort((a,b) => b.match_score - a.match_score));
            })
            .on('postgres_changes', {
                event: 'UPDATE',
                schema: 'public',
                table: 'screening_sessions',
                filter: `id=eq.${id}`
            }, (payload) => {
                setSession(payload.new);
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, [supabase, id]);

    const filteredResults = results.filter(r => 
        r.candidate_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.candidate_email.toLowerCase().includes(searchQuery.toLowerCase())
    ).filter(r => !r.is_dismissed);

    const toggleShortlist = async (resultId: string, current: boolean) => {
        const { error } = await supabase
            .from("screening_results")
            .update({ is_shortlisted: !current })
            .eq("id", resultId);
        
        if (!error) {
            setResults(prev => prev.map(r => r.id === resultId ? { ...r, is_shortlisted: !current } : r));
            if (selectedResult?.id === resultId) {
                setSelectedResult({ ...selectedResult, is_shortlisted: !current });
            }
        }
    };

    const dismissResult = async (resultId: string) => {
        const { error } = await supabase
            .from("screening_results")
            .update({ is_dismissed: true })
            .eq("id", resultId);
        
        if (!error) {
            setResults(prev => prev.filter(r => r.id !== resultId));
            if (selectedResult?.id === resultId) setSelectedResult(null);
        }
    };

    // Analytics Calculation
    const avgScore = results.length > 0 ? Math.round(results.reduce((acc, r) => acc + r.match_score, 0) / results.length) : 0;
    const topPerformers = results.filter(r => r.match_score >= 80).length;
    
    // Chart Data (Distribution)
    const distributionData = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90].map(bucket => ({
        range: `${bucket}-${bucket+10}`,
        count: results.filter(r => r.match_score >= bucket && r.match_score < bucket + 10).length
    }));

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!session) return <div>Cycle Matrix Not Found.</div>;

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-32">
             {/* Header */}
             <header className="flex flex-col space-y-8">
                <Link 
                    href="/dashboard/screening" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-secondary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Historical Archives</span>
                </Link>

                <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3 text-secondary">
                             <BarChart3 className="w-8 h-8" />
                             <span className="text-sm font-black uppercase tracking-widest italic decoration-2 underline decoration-secondary/20">Metric Hub Intelligence</span>
                        </div>
                        <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                            {session.title}
                        </h1>
                        <p className="text-gray-500 font-bold max-w-lg italic">
                           Ref: {session.job?.title || "Manual Reservoir"} • {session.total_files} Total Metrics Screened
                        </p>
                    </div>

                    <div className="flex items-center space-x-4">
                        <button className="px-8 py-5 bg-white border border-gray-100 rounded-[32px] font-black text-xs uppercase tracking-widest italic text-gray-500 hover:bg-gray-50 flex items-center space-x-2">
                            <Download className="w-4 h-4" />
                            <span>Export Matrix</span>
                        </button>
                        <button 
                            onClick={() => {
                                const shortlisted = results.filter(r => r.is_shortlisted);
                                if (shortlisted.length === 0) {
                                    alert("No candidates selected for deployment.");
                                    return;
                                }
                                // Deployment logic
                                alert(`Deploying ${shortlisted.length} candidates to mission: ${session.job?.title || "General Pool"}`);
                            }}
                            className="px-10 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-sm uppercase tracking-widest italic hover:scale-105 transition-all shadow-xl disabled:opacity-50"
                        >
                            Deploy Candidates
                        </button>
                    </div>
                </div>
            </header>

            {/* Compute Metrics Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                {[
                    { label: "Neural Efficiency", val: `${avgScore}%`, sub: "Average Metric Score", color: "text-primary", bg: "bg-primary/5" },
                    { label: "Critical Matches", val: topPerformers, sub: "Score >= 80%", color: "text-emerald-500", bg: "bg-emerald-50" },
                    { label: "Protocol Integrity", val: "100%", sub: "No failed metrics", color: "text-secondary", bg: "bg-secondary/5" },
                    { label: "Compute Time", val: "≈ 14.2s", sub: "Parallel vetting", color: "text-amber-500", bg: "bg-amber-50" }
                ].map((stat, i) => (
                    <div key={i} className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm space-y-4">
                         <div className={`w-12 h-12 rounded-2xl ${stat.bg} ${stat.color} flex items-center justify-center`}>
                             <Zap className="w-6 h-6" />
                         </div>
                         <div>
                            <h4 className="text-4xl font-black text-zinc-900 italic tracking-tighter leading-none">{stat.val}</h4>
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-2">{stat.label}</p>
                            <p className="text-[8px] font-bold text-gray-300 italic">{stat.sub}</p>
                         </div>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                 {/* Main List (2/3) */}
                 <div className="lg:col-span-2 space-y-8">
                     <div className="flex flex-col md:flex-row gap-4 items-center">
                        <div className="relative flex-1 group">
                            <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-secondary transition-colors" />
                            <input 
                                type="text"
                                placeholder="Scan results for names or email domains..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-16 pr-6 py-5 bg-white border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-secondary/5 transition-all"
                            />
                        </div>
                        <button className="px-6 py-5 bg-gray-50 border border-gray-100 rounded-[28px] font-black text-[10px] uppercase tracking-widest text-gray-400 hover:text-zinc-600 transition-all">
                            <Filter className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="bg-white border border-gray-100 rounded-[56px] overflow-hidden shadow-sm">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50 border-b border-gray-100">
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Candidate Metrics</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic text-center">Breakdown</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Neural Resonance</th>
                                    <th className="px-8 py-5 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {filteredResults.map((r) => (
                                    <tr 
                                        key={r.id} 
                                        className={`hover:bg-gray-50/30 transition-colors cursor-pointer group ${selectedResult?.id === r.id ? "bg-gray-50/50" : ""}`}
                                        onClick={() => setSelectedResult(r)}
                                    >
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-4">
                                                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-black text-xl italic shadow-sm overflow-hidden ${
                                                    r.match_score >= 80 ? "bg-emerald-50 text-emerald-500" :
                                                    r.match_score >= 50 ? "bg-primary/5 text-primary" : "bg-gray-50 text-gray-300"
                                                }`}>
                                                    {r.candidate_name[0]}
                                                </div>
                                                <div>
                                                    <h4 className="text-sm font-black text-zinc-900 italic tracking-tight">{r.candidate_name}</h4>
                                                    <p className="text-[10px] font-bold text-gray-400">{r.candidate_email}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-1 justify-center">
                                                {['skills', 'exp', 'edu', 'keyword', 'question'].map((scoreKey) => (
                                                    <div 
                                                        key={scoreKey}
                                                        className="w-1.5 h-6 bg-gray-50 rounded-full overflow-hidden" 
                                                        title={`${scoreKey}: ${r.analysis[`${scoreKey}_score`] || 0}%`}
                                                    >
                                                        <div 
                                                            className={`w-full h-full ${
                                                                scoreKey === 'skills' ? 'bg-primary' :
                                                                scoreKey === 'exp' ? 'bg-secondary' :
                                                                scoreKey === 'edu' ? 'bg-zinc-900' :
                                                                scoreKey === 'keyword' ? 'bg-emerald-500' : 'bg-amber-500'
                                                            }`}
                                                            style={{ height: `${r.analysis[`${scoreKey}_score`] || 0}%`, marginTop: 'auto' }}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center space-x-3">
                                                 <div className="w-24 h-1.5 bg-gray-50 rounded-full overflow-hidden">
                                                     <motion.div 
                                                        initial={{ width: 0 }}
                                                        animate={{ width: `${r.match_score}%` }}
                                                        className={`h-full ${
                                                            r.match_score >= 80 ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" :
                                                            r.match_score >= 50 ? "bg-primary shadow-[0_0_10px_rgba(0,102,255,0.4)]" : "bg-gray-300"
                                                        }`}
                                                     />
                                                 </div>
                                                 <span className="text-xs font-black text-zinc-900 italic">{r.match_score}%</span>
                                            </div>
                                        </td>
                                        <td className="px-8 py-6">
                                            <div className="flex items-center justify-end space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <button 
                                                    onClick={(e) => { e.stopPropagation(); toggleShortlist(r.id, r.is_shortlisted); }}
                                                    className={`p-2 rounded-lg border transition-all ${r.is_shortlisted ? "bg-amber-50 border-amber-200 text-amber-500" : "bg-white border-gray-100 text-gray-300 hover:text-amber-500"}`}
                                                >
                                                    <Star className={`w-4 h-4 ${r.is_shortlisted ? "fill-current" : ""}`} />
                                                </button>
                                                <button 
                                                    onClick={(e) => { e.stopPropagation(); dismissResult(r.id); }}
                                                    className="p-2 bg-white border border-gray-100 text-gray-300 hover:text-red-500 hover:border-red-100 rounded-lg transition-all"
                                                >
                                                    <XCircle className="w-4 h-4" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                 </div>

                 {/* Sidebar analytics (1/3) */}
                 <div className="space-y-8">
                      {/* Distribution Chart */}
                      <section className="bg-white border border-gray-100 rounded-[48px] p-8 shadow-sm space-y-6">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-black text-zinc-900 italic uppercase">Score Matrix</h3>
                                <PieChart className="w-4 h-4 text-gray-300" />
                            </div>
                            <div className="h-[200px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={distributionData}>
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                                        <XAxis 
                                            dataKey="range" 
                                            axisLine={false} 
                                            tickLine={false} 
                                            tick={{ fontSize: 8, fontWeight: 900, fill: '#9ca3af' }}
                                        />
                                        <YAxis hide />
                                        <Tooltip 
                                            cursor={{ fill: 'rgba(0,0,0,0.02)' }}
                                            contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)', fontSize: '10px', fontWeight: 900 }}
                                        />
                                        <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                                            {distributionData.map((entry, index) => (
                                                <Cell key={index} fill={index >= 7 ? '#10b981' : index >= 4 ? '#0066FF' : '#e5e7eb'} />
                                            ))}
                                        </Bar>
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                            <p className="text-[10px] text-gray-400 font-bold italic leading-relaxed text-center">Score distribution across all processed metrics within this simulation.</p>
                      </section>

                      {/* Detail Sidepanel (Overlays if needed, but here it's contextual) */}
                      <AnimatePresence mode="wait">
                          {selectedResult ? (
                              <motion.section 
                                key={selectedResult.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                className="bg-zinc-900 rounded-[48px] p-10 shadow-2xl space-y-10 text-white relative overflow-hidden"
                              >
                                  <div className="flex items-center justify-between">
                                       <button onClick={() => setSelectedResult(null)} className="p-2 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
                                           <ChevronLeft className="w-4 h-4" />
                                       </button>
                                       <div className="flex items-center space-x-2 text-primary">
                                           <Zap className="w-5 h-5 animate-pulse" />
                                           <span className="text-3xl font-black italic tracking-tighter">{selectedResult.match_score}%</span>
                                       </div>
                                  </div>

                                  <div className="space-y-4">
                                      <h3 className="text-3xl font-black italic tracking-tighter">{selectedResult.candidate_name}</h3>
                                      <div className="flex flex-wrap gap-2">
                                          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-[8px] font-black uppercase tracking-widest text-emerald-400 flex items-center space-x-2">
                                              <Users className="w-3 h-3" />
                                              <span>Exp: {selectedResult.analysis.exp_score}%</span>
                                          </div>
                                          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-[8px] font-black uppercase tracking-widest text-primary flex items-center space-x-2">
                                              <Briefcase className="w-3 h-3" />
                                              <span>Skills: {selectedResult.analysis.skills_score}%</span>
                                          </div>
                                          <div className="px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-[8px] font-black uppercase tracking-widest text-amber-400 flex items-center space-x-2">
                                              <MessageSquare className="w-3 h-3" />
                                              <span>Q&A: {selectedResult.analysis.question_score || 0}%</span>
                                          </div>
                                      </div>
                                  </div>

                                  <div className="space-y-6">
                                      <div className="space-y-4">
                                            <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Intelligence Summary</h5>
                                            <p className="text-xs text-gray-300 font-bold italic leading-relaxed">
                                                {selectedResult.analysis.summary}
                                            </p>
                                      </div>

                                      <div className="space-y-4 pt-6 border-t border-white/5">
                                            <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Core Constraints Matched</h5>
                                            <div className="flex flex-wrap gap-2">
                                                {selectedResult.analysis.keyword_matches.slice(0, 5).map((m: string, i: number) => (
                                                    <span key={i} className="px-3 py-1 bg-emerald-500 text-white rounded-lg text-[10px] font-black italic">{m}</span>
                                                ))}
                                            </div>
                                      </div>
                                  </div>

                                  <div className="pt-8">
                                       <Link 
                                            href={selectedResult.resume_url} 
                                            target="_blank"
                                            className="w-full py-4 bg-white text-zinc-900 rounded-3xl font-black text-[10px] uppercase tracking-widest italic flex items-center justify-center space-x-3 hover:bg-primary hover:text-white transition-all shadow-xl"
                                       >
                                           <Download className="w-4 h-4" />
                                           <span>Audit Resume PDF</span>
                                       </Link>
                                  </div>

                                  <div className="absolute right-0 bottom-0 w-48 h-48 bg-primary/20 blur-[100px] rounded-full translate-x-1/2 translate-y-1/2" />
                              </motion.section>
                          ) : (
                              <section className="bg-gray-50 border-2 border-dashed border-gray-100 rounded-[48px] p-16 text-center space-y-6 opacity-40 grayscale">
                                   <Info className="w-12 h-12 text-gray-300 mx-auto" />
                                   <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Select a Metric for Intelligence Deep Dive</p>
                              </section>
                          )}
                      </AnimatePresence>
                 </div>
            </div>
        </div>
    );
}
