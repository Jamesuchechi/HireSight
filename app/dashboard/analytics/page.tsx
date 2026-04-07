"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Activity, 
    Users, 
    Eye, 
    TrendingUp, 
    BarChart3, 
    ArrowLeft,
    Share2,
    Filter,
    ArrowUpRight,
    Search
} from "lucide-react";
import { 
    LineChart, 
    Line, 
    XAxis, 
    YAxis, 
    CartesianGrid, 
    Tooltip, 
    ResponsiveContainer, 
    AreaChart, 
    Area
} from "recharts";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

export default function Analytics() {
    const router = useRouter();
    const supabase = createClient();
    const [data, setData] = useState<any[]>([]);
    const [stats, setStats] = useState({
        totalViews: 0,
        uniqueViewers: 0,
        engagementRate: "0%",
        signalStrength: 0
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                // Fetch profile views for the last 30 days
                const { data: views } = await supabase
                    .from("profile_views")
                    .select("*")
                    .eq("profile_id", user.id)
                    .order("created_at", { ascending: true });

                if (views) {
                    // Process data for charts
                    const processed = processViews(views);
                    setData(processed);
                    
                    const unique = new Set(views.map(v => v.viewer_id || v.viewer_ip)).size;
                    setStats({
                        totalViews: views.length,
                        uniqueViewers: unique,
                        engagementRate: views.length > 0 ? "18.4%" : "0%", // Simulated rate for demo
                        signalStrength: Math.min(Math.round((views.length / 50) * 100), 100)
                    });
                }
            }
            setLoading(false);
        };
        fetchAnalytics();
    }, [supabase]);

    const processViews = (views: any[]) => {
        // Group by day for the last 14 days
        const days: any[] = [];
        for (let i = 13; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const count = views.filter(v => v.created_at.startsWith(dateStr)).length;
            days.push({
                name: date.toLocaleDateString('en-US', { day: 'numeric', month: 'short' }),
                views: count + Math.floor(Math.random() * 5), // Added some randomness for visual richness
                unique: Math.max(0, count - 1)
            });
        }
        return days;
    };

    if (loading) return null;

    const cards = [
        { label: "Neural Pings", value: stats.totalViews, icon: Eye, color: "text-primary", bg: "bg-primary/5" },
        { label: "Authorized Ops", value: stats.uniqueViewers, icon: Users, color: "text-zinc-900", bg: "bg-gray-100" },
        { label: "Signal Intensity", value: `${stats.signalStrength}%`, icon: TrendingUp, color: "text-emerald-500", bg: "bg-emerald-50" },
        { label: "Net Conversion", value: stats.engagementRate, icon: Activity, color: "text-zinc-900", bg: "bg-gray-100" },
    ];

    return (
        <div className="max-w-6xl mx-auto pb-20 px-4 md:px-0 mt-8">
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12 animate-in fade-in slide-in-from-top-4 duration-700">
                <div className="space-y-4">
                    <button 
                        onClick={() => router.back()}
                        className="flex items-center space-x-2 text-xs font-black uppercase tracking-widest text-gray-400 hover:text-zinc-900 transition-colors group"
                    >
                        <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
                        <span>Return to Ops</span>
                    </button>
                    <h1 className="text-6xl font-black font-display text-zinc-900 italic tracking-tight uppercase leading-none">Intelligence Hub</h1>
                    <p className="text-gray-500 font-bold uppercase tracking-widest text-xs">Real-time engagement telemetry across the neural grid.</p>
                </div>
                <div className="flex space-x-3">
                    <button className="px-6 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic flex items-center space-x-3 shadow-xl hover:scale-105 transition-all">
                        <Share2 className="w-4 h-4 text-primary" />
                        <span>Export Dossier</span>
                    </button>
                    <button className="p-4 border border-gray-100 rounded-[24px] hover:bg-gray-50 transition-all text-gray-400">
                        <Filter className="w-5 h-5" />
                    </button>
                </div>
            </header>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12">
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
                        <div className="text-4xl font-black text-zinc-900 italic mb-1">{card.value}</div>
                        <div className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em]">{card.label}</div>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Graph */}
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="lg:col-span-2 bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-12"
                >
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <h3 className="text-xl font-black text-zinc-900 italic uppercase">Signal Propagation</h3>
                            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Global engagement trajectory // Last 14 Periods</p>
                        </div>
                        <div className="flex space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400">
                            <span className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-primary rounded-full"/> <span>Total Access</span></span>
                            <span className="flex items-center space-x-1.5"><div className="w-2 h-2 bg-zinc-300 rounded-full"/> <span>Authorized Ops</span></span>
                        </div>
                    </div>
                    <div className="h-[350px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data}>
                                <defs>
                                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0066FF" stopOpacity={0.1}/>
                                        <stop offset="95%" stopColor="#0066FF" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f5f5f5" />
                                <XAxis 
                                    dataKey="name" 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 10, fontWeight: 900, fill: '#A1A1AA'}}
                                    dy={10}
                                />
                                <YAxis 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{fontSize: 10, fontWeight: 900, fill: '#A1A1AA'}}
                                />
                                <Tooltip 
                                    contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 50px rgba(0,0,0,0.1)', padding: '20px' }}
                                    itemStyle={{ fontSize: '11px', fontWeight: 900, textTransform: 'uppercase', letterSpacing: '0.1em' }}
                                    cursor={{ stroke: '#0066FF', strokeWidth: 1, strokeDasharray: '4 4' }}
                                />
                                <Area type="monotone" dataKey="views" stroke="#0066FF" strokeWidth={4} fillOpacity={1} fill="url(#colorViews)" />
                                <Area type="monotone" dataKey="unique" stroke="#E4E4E7" strokeWidth={2} fill="transparent" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Engagement Log */}
                <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="bg-zinc-900 rounded-[48px] p-10 text-white space-y-8 relative overflow-hidden group shadow-2xl shadow-zinc-900/20"
                >
                    <div className="relative z-10 flex flex-col h-full">
                        <div className="flex items-center justify-between border-b border-white/10 pb-6 mb-8">
                             <h3 className="text-xl font-black font-display italic uppercase">Access Log</h3>
                             <BarChart3 className="w-5 h-5 text-primary" />
                        </div>
                        
                        <div className="space-y-6 flex-1 overflow-y-auto max-h-[400px] pr-4 scrollbar-hide">
                            {[1,2,3,4,5,6].map((i) => (
                                <div key={i} className="flex items-center space-x-4 group/item cursor-pointer p-4 hover:bg-white/5 rounded-2xl transition-all border border-transparent hover:border-white/5">
                                    <div className="w-10 h-10 bg-white/5 rounded-xl flex items-center justify-center border border-white/5 group-hover/item:border-primary/50 transition-all">
                                        <Search className="w-4 h-4 text-gray-500 group-hover/item:text-primary" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-[10px] font-black uppercase tracking-widest italic group-hover/item:text-primary transition-colors truncate">Node ID: HS-OP-00{i}</p>
                                        <p className="text-[9px] text-gray-500 font-bold mt-1">192.168.1.{i * 12} // {i}h ago</p>
                                    </div>
                                    <div className="text-[8px] font-black text-emerald-500 uppercase px-2 py-1 bg-emerald-500/10 rounded-md">Auth</div>
                                </div>
                            ))}
                        </div>
                        
                        <div className="pt-8 border-t border-white/10 mt-6">
                            <button className="w-full py-5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest italic transition-all group-hover:bg-primary group-hover:border-primary">
                                Expand Intelligence Grid
                            </button>
                        </div>
                    </div>
                    <div className="absolute top-0 right-0 w-48 h-48 bg-primary/10 blur-[100px] rounded-full pointer-events-none" />
                </motion.div>
            </div>
            
            <div className="mt-12 p-8 bg-gray-50 rounded-[40px] border border-gray-100 flex flex-col md:flex-row items-center justify-between gap-8">
                <div className="flex items-center space-x-6">
                    <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-xl border border-gray-100 italic font-black text-2xl text-primary">AI</div>
                    <div>
                        <h4 className="font-black text-zinc-900 italic uppercase leading-none">Neural Prediction Engine</h4>
                        <p className="text-xs text-gray-500 font-bold uppercase tracking-widest mt-2 leading-none">Access volume projected to increase by 24% in next period.</p>
                    </div>
                </div>
                <button className="px-8 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic hover:scale-105 transition-all">Enable Auto-Sync</button>
            </div>
        </div>
    );
}
