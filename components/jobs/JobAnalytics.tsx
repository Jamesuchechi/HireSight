"use client";

import { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, 
    Tooltip, ResponsiveContainer, LineChart, Line,
    AreaChart, Area 
} from "recharts";
import { 
    Users, Eye, MousePointer2, TrendingUp, 
    ArrowUpRight, ArrowDownRight, Clock, Target 
} from "lucide-react";
import { Database } from "@/types/database";

interface AnalyticsData {
    viewsByDate: { date: string; count: number }[];
    appsByDate: { date: string; count: number }[];
    totalViews: number;
    totalApps: number;
    avgMatchScore: number;
}

export default function JobAnalytics({ data }: { data: AnalyticsData }) {
    const appRate = data.totalViews > 0 ? ((data.totalApps / data.totalViews) * 100).toFixed(1) : "0";

    const combinedData = data.viewsByDate.map((v, i) => ({
        date: v.date,
        views: v.count,
        applications: data.appsByDate[i]?.count || 0
    }));

    return (
        <div className="space-y-10">
            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard 
                    title="Total Views" 
                    value={data.totalViews} 
                    icon={<Eye />} 
                    color="text-primary" 
                    bg="bg-primary/5" 
                />
                <StatCard 
                    title="Applications" 
                    value={data.totalApps} 
                    icon={<Users />} 
                    color="text-secondary" 
                    bg="bg-secondary/5" 
                />
                <StatCard 
                    title="App Rate" 
                    value={`${appRate}%`} 
                    icon={<MousePointer2 />} 
                    color="text-emerald-500" 
                    bg="bg-emerald-50" 
                />
                <StatCard 
                    title="Avg Match" 
                    value={`${data.avgMatchScore}%`} 
                    icon={<Target />} 
                    color="text-accent" 
                    bg="bg-accent/5" 
                />
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Traffic Chart */}
                <div className="lg:col-span-2 bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm">
                    <div className="flex items-center justify-between mb-8">
                        <div>
                            <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Traffic Vector</h3>
                            <p className="text-[10px] text-gray-400 font-black uppercase tracking-[0.2em] mt-1">Daily Views vs Applications</p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 rounded-full bg-primary" />
                                <span className="text-[10px] font-black text-gray-400 uppercase">Views</span>
                            </div>
                             <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 rounded-full bg-secondary" />
                                <span className="text-[10px] font-black text-gray-400 uppercase">Apps</span>
                            </div>
                        </div>
                    </div>

                    <div className="h-[350px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={combinedData}>
                                <defs>
                                    <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#0066FF" stopOpacity={0.1}/>
                                        <stop offset="95%" stopColor="#0066FF" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorApps" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.1}/>
                                        <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                                <XAxis 
                                    dataKey="date" 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{ fontSize: 10, fontWeight: 900, fill: '#9CA3AF' }}
                                    dy={10}
                                />
                                <YAxis 
                                    axisLine={false} 
                                    tickLine={false} 
                                    tick={{ fontSize: 10, fontWeight: 900, fill: '#9CA3AF' }}
                                />
                                <Tooltip 
                                    contentStyle={{ 
                                        borderRadius: '20px', 
                                        border: 'none', 
                                        boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)',
                                        padding: '12px'
                                    }}
                                />
                                <Area type="monotone" dataKey="views" stroke="#0066FF" strokeWidth={3} fillOpacity={1} fill="url(#colorViews)" />
                                <Area type="monotone" dataKey="applications" stroke="#00D4FF" strokeWidth={3} fillOpacity={1} fill="url(#colorApps)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Secondary Stats */}
                <div className="space-y-8">
                     <div className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm">
                         <h4 className="text-sm font-black font-display text-zinc-900 mb-6 italic uppercase">Time to Deploy</h4>
                         <div className="flex items-end justify-between">
                            <div className="space-y-1">
                                <h5 className="text-4xl font-black text-primary italic">2.4<span className="text-lg">d</span></h5>
                                <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest">Avg to first app</p>
                            </div>
                            <Clock className="w-10 h-10 text-primary/10" />
                         </div>
                         <div className="mt-6 pt-6 border-t border-gray-50">
                            <div className="flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-gray-400">
                                <span>Optimization</span>
                                <span className="text-emerald-500">Fast Mode</span>
                            </div>
                            <div className="w-full h-1.5 bg-gray-50 rounded-full mt-2 overflow-hidden">
                                <div className="w-[85%] h-full bg-emerald-500 rounded-full" />
                            </div>
                         </div>
                     </div>

                     <div className="bg-zinc-900 rounded-[40px] p-8 shadow-2xl relative overflow-hidden group">
                         <div className="relative z-10 space-y-4">
                            <h4 className="text-sm font-black text-white italic tracking-widest uppercase">Export Protocol</h4>
                            <p className="text-xs text-gray-400 font-bold leading-relaxed italic">Download the full analytical matrix for this opportunity in CSV or PDF format.</p>
                            <button className="w-full py-3 bg-white text-zinc-900 rounded-xl font-black text-[10px] uppercase tracking-widest italic flex items-center justify-center space-x-2 hover:bg-primary hover:text-white transition-all">
                                <span>Extract Data</span>
                                <ArrowUpRight className="w-3 h-3" />
                            </button>
                         </div>
                         <div className="absolute -right-10 -bottom-10 w-32 h-32 bg-primary/20 blur-3xl rounded-full" />
                     </div>
                </div>
            </div>
        </div>
    );
}

function StatCard({ title, value, icon, color, bg }: any) {
    return (
        <div className="bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm hover:shadow-xl transition-all group relative overflow-hidden">
            <div className={`p-4 rounded-2xl ${bg} ${color} inline-flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                {icon}
            </div>
            <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-1 italic">{title}</p>
            <div className="flex items-end justify-between">
                <h4 className="text-4xl font-black text-zinc-900 italic tracking-tighter">{value}</h4>
            </div>
            <div className={`absolute -right-4 -bottom-4 w-20 h-20 ${bg} opacity-[0.03] rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700`} />
        </div>
    );
}
