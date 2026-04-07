"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    TrendingUp, 
    Users, 
    Eye, 
    Zap, 
    ArrowLeft, 
    FileText, 
    Share2, 
    MoreVertical,
    Target,
    BarChart3,
    ArrowUpRight,
    Search,
    ChevronRight,
    Download
} from "lucide-react";
import { 
    ResponsiveContainer, 
    AreaChart, 
    Area, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip,
    BarChart,
    Bar,
    Cell
} from "recharts";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function JobAnalyticsPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    
    const [job, setJob] = useState<any>(null);
    const [analytics, setAnalytics] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [trends, setTrends] = useState<any[]>([]);

    useEffect(() => {
        const fetchJobData = async () => {
            const { data: jobData } = await supabase
                .from("jobs")
                .select("*")
                .eq("id", id)
                .single();
            setJob(jobData);

            const { data: analyticsData } = await supabase.rpc('get_job_analytics', { jid: id });
            setAnalytics(analyticsData);

            // Mock historical trend for this job specifically
            const mockTrends = [];
            for (let i = 14; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                mockTrends.push({
                    name: date.toLocaleDateString('en-US', { day: 'numeric', month: 'short' }),
                    views: Math.floor(Math.random() * 12) + (analyticsData?.views || 0) / 15,
                    apps: Math.floor(Math.random() * 3) + (analyticsData?.total_applications || 0) / 15
                });
            }
            setTrends(mockTrends);
            
            setLoading(false);
        };
        fetchJobData();
    }, [id, supabase]);

    if (loading) return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Decrypting Job Metrics...</p>
        </div>
    );

    const funnelData = [
        { name: 'Views', value: analytics?.views || 0, fill: '#F1F5F9' },
        { name: 'Applied', value: analytics?.funnel?.applied || 0, fill: '#0066FF' },
        { name: 'Screening', value: analytics?.funnel?.screening || 0, fill: '#3B82F6' },
        { name: 'Interview', value: analytics?.funnel?.interviews || 0, fill: '#60A5FA' },
        { name: 'Offer/Hired', value: analytics?.funnel?.offers || 0, fill: '#10B981' },
    ];

    const cards = [
        { label: "Neural Pings", value: analytics?.views, icon: Eye, color: "text-primary", bg: "bg-primary/5" },
        { label: "Submissions", value: analytics?.total_applications, icon: FileText, color: "text-zinc-900", bg: "bg-gray-100" },
        { label: "Fresh Contacts", value: analytics?.applications_today, icon: Zap, color: "text-emerald-500", bg: "bg-emerald-50" },
        { label: "Conversion rate", value: `${Math.round(analytics?.conversion_rate || 0)}%`, icon: TrendingUp, color: "text-zinc-900", bg: "bg-gray-100" },
    ];

    return (
        <div className="max-w-7xl mx-auto pb-24 space-y-12">
            {/* Header Strategy */}
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-8 animate-in fade-in slide-in-from-top-4 duration-700">
                <div className="space-y-4">
                    <button 
                        onClick={() => router.back()}
                        className="flex items-center space-x-2 text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 hover:text-zinc-900 transition-colors group italic"
                    >
                        <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
                        <span>Return to Fleet Management</span>
                    </button>
                    <div className="flex items-center space-x-3 mb-2">
                        <span className="px-3 py-1 bg-primary/10 text-primary text-[8px] font-black uppercase tracking-widest rounded-lg border border-primary/20 italic">
                            Mission Analytics
                        </span>
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest italic">Live Feed</span>
                    </div>
                    <h1 className="text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none mb-1">
                        {job?.title}
                    </h1>
                    <p className="text-gray-500 font-bold uppercase tracking-widest text-[10px]">Deep Intel Extraction // Objective ID: {id.substring(0, 8)}</p>
                </div>
                <div className="flex space-x-3">
                    <button 
                        onClick={() => window.print()}
                        className="px-6 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic flex items-center space-x-3 shadow-xl hover:scale-105 transition-all"
                    >
                        <Download className="w-4 h-4 text-primary" />
                        <span>Generate Intelligence Dossier</span>
                    </button>
                </div>
            </header>

            {/* KPI Matrix */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {cards.map((card, i) => (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        key={i} 
                        className={`p-8 ${card.bg} rounded-[40px] border border-transparent hover:border-zinc-900/5 transition-all group`}
                    >
                        <div className="flex justify-between items-start mb-6">
                            <card.icon className={`w-8 h-8 ${card.color} opacity-60`} />
                            <ArrowUpRight className="w-4 h-4 text-gray-300 group-hover:text-zinc-900 transition-colors" />
                        </div>
                        <div className="text-4xl font-black text-zinc-900 italic mb-1">{card.value || 0}</div>
                        <div className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">{card.label}</div>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* Engagement Trends */}
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="lg:col-span-8 bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-12"
                >
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <h3 className="text-xl font-black text-zinc-900 italic uppercase">Interest Propagation</h3>
                            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Views vs Applications Tracking // Fortnightly View</p>
                        </div>
                        <div className="flex space-x-4 text-[10px] font-black uppercase tracking-widest text-gray-400">
                             <span className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-primary rounded-full"/> <span>Neural Pings</span></span>
                             <span className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-zinc-900 rounded-full"/> <span>Deployments</span></span>
                        </div>
                    </div>
                    <div className="h-[400px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={trends}>
                                <defs>
                                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0066FF" stopOpacity={0.1}/>
                                        <stop offset="95%" stopColor="#0066FF" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                                <XAxis 
                                    dataKey="name" 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 9, fontWeight: 900, fill: '#A1A1AA'}}
                                    dy={10}
                                />
                                <YAxis 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 9, fontWeight: 900, fill: '#A1A1AA'}}
                                />
                                <Tooltip 
                                    contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 50px rgba(0,0,0,0.1)', padding: '20px' }}
                                    itemStyle={{ fontSize: '10px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}
                                />
                                <Area type="monotone" dataKey="views" stroke="#0066FF" strokeWidth={4} fillOpacity={1} fill="url(#colorViews)" />
                                <Area type="monotone" dataKey="apps" stroke="#18181B" strokeWidth={2} fill="transparent" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Pipeline Funnel */}
                <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="lg:col-span-4 space-y-8"
                >
                     <div className="bg-zinc-900 rounded-[48px] p-10 text-white space-y-10 relative overflow-hidden shadow-2xl h-full">
                        <div className="relative z-10 flex flex-col h-full">
                             <div className="flex items-center justify-between border-b border-white/10 pb-6 mb-8">
                                 <h3 className="text-xl font-black font-display italic uppercase">Protocol Funnel</h3>
                                 <BarChart3 className="w-5 h-5 text-primary" />
                            </div>

                            <div className="flex-1 space-y-6">
                                {funnelData.map((stage, i) => (
                                    <div key={stage.name} className="space-y-2">
                                        <div className="flex justify-between items-end">
                                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 italic">{stage.name}</span>
                                            <span className="text-lg font-black italic">{stage.value}</span>
                                        </div>
                                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                                            <motion.div 
                                                initial={{ width: 0 }}
                                                animate={{ width: `${(stage.value / (funnelData[0].value || 1)) * 100}%` }}
                                                transition={{ delay: 0.8 + (i * 0.1), duration: 1.2, ease: "circOut" }}
                                                className="h-full"
                                                style={{ backgroundColor: stage.fill }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="pt-8 mt-12 border-t border-white/10">
                                <Link 
                                    href={`/dashboard/jobs/${id}/applicants`}
                                    className="w-full py-5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest italic flex items-center justify-center space-x-3 transition-all"
                                >
                                    <span>Access Candidate Pipeline</span>
                                    <ChevronRight className="w-4 h-4" />
                                </Link>
                            </div>
                        </div>
                        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 blur-[100px] rounded-full pointer-events-none" />
                    </div>
                </motion.div>
            </div>

            {/* Diversity / Skills Breakdown Mock */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm flex items-center space-x-8">
                    <div className="w-16 h-16 bg-emerald-50 rounded-[20px] flex items-center justify-center text-emerald-600">
                        <Target className="w-8 h-8" />
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Sector Precision</h4>
                        <p className="text-xl font-black text-zinc-900 italic tracking-tighter">94.2% AI-Candidate Alignment Score</p>
                    </div>
                </div>
                <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm flex items-center space-x-8">
                    <div className="w-16 h-16 bg-primary/5 rounded-[20px] flex items-center justify-center text-primary">
                        <Search className="w-8 h-8" />
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1">Search Impact</h4>
                        <p className="text-xl font-black text-zinc-900 italic tracking-tighter">Appearing in 482 Search Queries This Cycle</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
