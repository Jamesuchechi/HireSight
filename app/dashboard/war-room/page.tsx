"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Zap, Activity, ShieldCheck, 
    Users, Target, BrainCircuit,
    ArrowUpRight, ArrowDownRight,
    Search, Filter, LayoutGrid
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { 
    BarChart, Bar, XAxis, YAxis, 
    CartesianGrid, Tooltip, ResponsiveContainer,
    AreaChart, Area
} from "recharts";
import MissionScanner from "@/components/war-room/MissionScanner";
import IntelligenceTicker from "@/components/war-room/IntelligenceTicker";
import ConsensusHub from "@/components/war-room/ConsensusHub";

export default function WarRoomPage() {
    const supabase = createClient();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<any>({
        activeEngagements: 0,
        throughputRate: 0,
        avgNeuralScore: 0,
        pipelineHealth: []
    });
    const [intelligenceLogs, setIntelligenceLogs] = useState<any[]>([]);
    const [selectedConsensusApp, setSelectedConsensusApp] = useState<string | null>(null);

    useEffect(() => {
        const fetchWarRoomData = async () => {
            setLoading(true);
            
            // 1. Fetch Active Sessions
            const { data: activeSessions } = await supabase
                .from('interviews')
                .select('id')
                .in('status', ['scheduled', 'rescheduled']);

            // 2. Fetch Throughput (Aggregated Applications)
            const { data: apps } = await supabase
                .from('job_applications')
                .select('status');
            
            const throughput = [
                { name: 'Sourced', value: apps?.filter(a => a.status === 'applied').length || 0 },
                { name: 'Screened', value: apps?.filter(a => a.status === 'screening').length || 0 },
                { name: 'Technical', value: apps?.filter(a => a.status === 'technical_round').length || 0 },
                { name: 'Behavioral', value: apps?.filter(a => a.status === 'behavioral_round').length || 0 },
                { name: 'Final', value: apps?.filter(a => a.status === 'final_round').length || 0 },
                { name: 'Offered', value: apps?.filter(a => a.status === 'offered').length || 0 },
            ];

            // 3. Fetch Recent Intelligence (Feedback)
            const { data: feedback } = await supabase
                .from('interview_feedback')
                .select(`
                    id, 
                    overall_score, 
                    comments, 
                    created_at,
                    interview:interviews(
                        type,
                        job_application:job_applications(
                            candidate:profiles!candidate_id(full_name)
                        )
                    )
                `)
                .order('created_at', { ascending: false })
                .limit(10);

            const logs = feedback?.map(f => {
                const interview = f.interview as any;
                return {
                    id: f.id,
                    type: 'assessment',
                    protocol: interview?.type === 'technical' ? 'live' : 'training',
                    candidate_name: interview?.job_application?.candidate?.full_name || "Unknown Asset",
                    message: f.comments || "Mission protocol concluded with automated debrief.",
                    score: f.overall_score,
                    created_at: f.created_at
                };
            }) || [];

            // 4. Calculate Radar Intelligence
            const radarData = [
                { subject: 'Technical', A: logs.filter(l => l.protocol === 'live').reduce((acc, curr) => acc + (curr.score * 20), 0) / (logs.filter(l => l.protocol === 'live').length || 1), fullMark: 100 },
                { subject: 'Behavioral', A: 85, fullMark: 100 },
                { subject: 'Strategy', A: 72, fullMark: 100 },
                { subject: 'Alignment', A: 90, fullMark: 100 },
                { subject: 'Velocity', A: 88, fullMark: 100 },
            ];

            setStats({
                activeEngagements: activeSessions?.length || 0,
                throughputRate: 84, 
                avgNeuralScore: Math.round(logs.reduce((acc, curr) => acc + (curr.score * 20), 0) / (logs.length || 1)),
                pipelineHealth: throughput,
                radarData
            });
            setIntelligenceLogs(logs);
            setLoading(false);
        };

        fetchWarRoomData();

        // Realtime Subscription
        const channel = supabase.channel('war_room_sync')
            .on('postgres_changes' as any, { event: '*', table: 'interviews' }, () => fetchWarRoomData())
            .on('postgres_changes' as any, { event: '*', table: 'interview_feedback' }, () => fetchWarRoomData())
            .subscribe();

        return () => { supabase.removeChannel(channel); };
    }, [supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-10 pb-20 text-zinc-900 relative">
            <AnimatePresence>
                {selectedConsensusApp && (
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed inset-0 z-[100] flex items-center justify-center p-6 lg:p-12"
                    >
                        <div className="absolute inset-0 bg-zinc-950/80 backdrop-blur-3xl" onClick={() => setSelectedConsensusApp(null)} />
                        <div className="relative w-full max-w-6xl max-h-[90vh] overflow-y-auto scrollbar-hide">
                            <button 
                                onClick={() => setSelectedConsensusApp(null)}
                                className="absolute top-8 right-8 z-[110] p-4 bg-white/10 rounded-2xl text-white hover:bg-white/20 transition-all border border-white/10 group"
                            >
                                <Zap className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                            </button>
                            <ConsensusHub applicationId={selectedConsensusApp} />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
            {/* Background Atmosphere */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 blur-[120px] rounded-full translate-x-1/2 -translate-y-1/2" />
                <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-indigo-500/5 blur-[120px] rounded-full -translate-x-1/2 translate-y-1/2" />
            </div>

            {/* Tactical Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                <div className="space-y-2">
                    <div className="flex items-center space-x-4">
                         <div className="p-3 bg-zinc-900 text-white rounded-[20px] shadow-2xl">
                             <Target className="w-6 h-6" />
                         </div>
                         <span className="text-[10px] font-black text-zinc-900 uppercase tracking-[0.4em] italic underline decoration-2 decoration-primary/20">Strategic War Room</span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter uppercase leading-none">
                        Mission <span className="text-primary italic">Intelligence</span>
                    </h1>
                    <p className="text-lg font-bold text-gray-500 italic">High-velocity talent orchestration & tactical analysis.</p>
                </div>

                <div className="flex items-center space-x-3 bg-gray-100 p-2 rounded-3xl">
                    <div className="px-4 py-2 bg-white rounded-2xl shadow-sm text-[10px] font-black uppercase tracking-widest italic flex items-center space-x-2">
                        <Activity className="w-3 h-3 text-primary animate-pulse" />
                        <span>Live Protocol Feed Active</span>
                    </div>
                </div>
            </header>

            {/* Tactical Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                
                {/* 1. Performance Matrix (Recharts) */}
                <div className="lg:col-span-3 space-y-8">
                    {/* Key Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <MetricCard 
                            icon={<Zap className="w-4 h-4" />}
                            label="Active Missions" 
                            value={stats.activeEngagements} 
                            trend="+12%" 
                            isUp={true} 
                        />
                        <MetricCard 
                            icon={<ShieldCheck className="w-4 h-4" />}
                            label="Neural Score Avg" 
                            value={`${stats.avgNeuralScore}%`} 
                            trend="+2.4%" 
                            isUp={true} 
                        />
                        <MetricCard 
                            icon={<Users className="w-4 h-4" />}
                            label="Pipeline Throughput" 
                            value={stats.throughputRate} 
                            trend="-4.1%" 
                            isUp={false} 
                        />
                    </div>

                    {/* Funnel Throughput Chart */}
                    <div className="bg-white p-10 rounded-[48px] border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-2xl transition-all duration-500">
                        <div className="flex items-center justify-between mb-10">
                            <div>
                                <h3 className="text-2xl font-black italic tracking-tighter uppercase">Pipeline <span className="text-primary">Volatility</span></h3>
                                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic leading-none mt-1">Real-time throughput analysis</p>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-2xl group-hover:bg-primary group-hover:text-white transition-all">
                                <LayoutGrid className="w-6 h-6" />
                            </div>
                        </div>

                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={stats.pipelineHealth} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                                    <defs>
                                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.8}/>
                                            <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.1}/>
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f4f4f5" />
                                    <XAxis 
                                        dataKey="name" 
                                        axisLine={false} 
                                        tickLine={false}
                                        tick={{ fill: '#a1a1aa', fontSize: 10, fontWeight: '900' }}
                                    />
                                    <YAxis hide />
                                    <Tooltip 
                                        cursor={{ fill: '#fafafa' }}
                                        contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)', padding: '20px' }}
                                        labelStyle={{ fontWeight: '900', color: '#f43f5e', textTransform: 'uppercase', marginBottom: '8px', fontSize: '10px' }}
                                    />
                                    <Bar dataKey="value" fill="url(#barGradient)" radius={[12, 12, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Active Deployment Radar (Scanning View) */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                         <div className="bg-zinc-900 rounded-[56px] p-12 text-white overflow-hidden relative group">
                             <div className="relative z-10 flex flex-col h-full">
                                 <div className="space-y-1 mb-8">
                                     <h3 className="text-3xl font-black italic tracking-tighter uppercase">Protocol <span className="text-primary italic">Scanner</span></h3>
                                     <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic leading-none">Scanning active mission zones</p>
                                 </div>
                                 <MissionScanner data={stats.radarData} />
                             </div>
                             <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[100px] rounded-full -translate-x-1/2 -translate-y-1/2" />
                         </div>

                         <div className="bg-white rounded-[56px] p-12 border border-gray-100 shadow-sm flex flex-col">
                             <div className="space-y-1 mb-8">
                                 <h3 className="text-3xl font-black italic tracking-tighter uppercase">Tactical <span className="text-gray-400 italic">Objectives</span></h3>
                                 <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic leading-none">Operational priorities for this cycle</p>
                             </div>
                             
                             <div className="space-y-6 flex-grow">
                                 <ObjectiveItem label="Finalize Tech Review (Ghost-1)" status="critical" />
                                 <ObjectiveItem label="Deploy Behavioral Protcols (12)" status="pending" />
                                 <ObjectiveItem label="Initial Neural Sweep (30)" status="completed" />
                                 <ObjectiveItem label="Audit Privacy Consents" status="pending" />
                             </div>

                             <button className="w-full mt-8 py-5 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-[0.3em] hover:bg-primary transition-all italic">
                                 Broadcast Briefing
                             </button>
                         </div>
                    </div>
                </div>

                {/* 2. Intelligence Side Feed */}
                <div className="lg:col-span-1">
                    <IntelligenceTicker 
                        logs={intelligenceLogs} 
                        onLogClick={(log) => setSelectedConsensusApp(log.id)}
                    />
                </div>
            </div>
        </div>
    );
}

function MetricCard({ icon, label, value, trend, isUp }: any) {
    return (
        <div className="bg-white p-8 rounded-[40px] border border-gray-100 shadow-sm group hover:shadow-xl transition-all duration-500 overflow-hidden relative">
            <div className="relative z-10">
                <div className="flex items-center justify-between mb-4">
                    <div className="p-3 bg-gray-50 rounded-2xl group-hover:bg-primary/10 group-hover:text-primary transition-all">
                        {icon}
                    </div>
                    <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${isUp ? 'text-emerald-500 bg-emerald-50' : 'text-red-500 bg-red-50'}`}>
                        {isUp ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        <span className="text-[10px] font-black italic">{trend}</span>
                    </div>
                </div>
                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1 italic">{label}</p>
                <div className="flex items-baseline space-x-1">
                    <h4 className="text-3xl font-black italic tracking-tighter text-zinc-900 group-hover:scale-105 transition-transform origin-left">{value}</h4>
                </div>
            </div>
            <div className="absolute top-0 right-0 w-24 h-24 bg-primary/5 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
    );
}

function ObjectiveItem({ label, status }: any) {
    return (
        <div className="flex items-center justify-between group/item">
            <div className="flex items-center space-x-4">
                <div className={`w-2 h-2 rounded-full ${
                    status === 'critical' ? 'bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]' :
                    status === 'completed' ? 'bg-emerald-500' : 'bg-gray-200'
                }`} />
                <span className="text-sm font-bold text-zinc-900 italic group-hover/item:text-primary transition-colors">{label}</span>
            </div>
            <span className={`text-[8px] font-black uppercase tracking-widest italic ${
                 status === 'critical' ? 'text-red-500' :
                 status === 'completed' ? 'text-emerald-500' : 'text-gray-400'
            }`}>{status}</span>
        </div>
    );
}
