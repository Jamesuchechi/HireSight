"use client";

import { motion } from "framer-motion";
import { 
    TrendingUp, Send, Zap, Star, Clock, 
    Briefcase, MapPin, Users, ArrowUpRight,
    Calendar, CheckCircle2, ChevronRight,
    Search, Rocket, FileText, BrainCircuit
} from "lucide-react";
import Link from "next/link";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";

// --- REUSABLE STAT CARD ---
export const StatCard = ({ icon, title, value, sub, color, delay = 0 }: any) => (
    <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay }}
        className="p-8 bg-white border border-gray-100 rounded-[40px] shadow-sm hover:shadow-xl transition-all group overflow-hidden relative"
    >
        <div className={`w-14 h-14 rounded-2xl ${color} bg-opacity-10 text-opacity-100 flex items-center justify-center mb-6 transition-transform group-hover:scale-110 shadow-sm`}>
            {icon}
        </div>
        <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-2">{title}</p>
        <h4 className="text-4xl font-black text-zinc-900 italic tracking-tighter leading-none">{value}</h4>
        {sub && <p className="text-[8px] font-black text-emerald-500 uppercase tracking-widest mt-3 flex items-center">
            <TrendingUp className="w-3 h-3 mr-1" /> {sub}
        </p>}
        {/* Background decorative element */}
        <div className={`absolute -right-8 -bottom-8 w-32 h-32 ${color} opacity-[0.03] rounded-full blur-[60px] group-hover:scale-150 transition-all duration-1000`} />
    </motion.div>
);

// --- PROGRESS CIRCLE ---
export const ProfileProgress = ({ score }: { score: number }) => (
    <div className="bg-white border border-gray-100 shadow-sm rounded-[48px] p-10 flex flex-col items-center text-center space-y-6">
        <h4 className="text-sm font-black uppercase tracking-widest text-zinc-900 italic">Neural Integrity</h4>
        <div className="relative w-48 h-48">
            <svg className="w-full h-full transform -rotate-90">
                <circle cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="16" fill="transparent" className="text-gray-50" />
                <motion.circle 
                    cx="96" cy="96" r="80" stroke="currentColor" strokeWidth="16" fill="transparent" 
                    strokeDasharray="502" 
                    initial={{ strokeDashoffset: 502 }}
                    animate={{ strokeDashoffset: 502 - (502 * score) / 100 }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="text-primary transition-all shadow-lg"
                    strokeLinecap="round"
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-5xl font-black italic text-zinc-900 tracking-tighter">{score}%</span>
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">Synchronized</span>
            </div>
            {/* Glow effect */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-primary/10 blur-3xl rounded-full -z-10 animate-pulse" />
        </div>
        <p className="text-xs font-bold text-gray-500 leading-relaxed max-w-[200px]">
           Complete your protocol nodes to achieve maximum visibility in the recruiter matrix.
        </p>
    </div>
);

// --- RECRUITER FUNNEL ---
export const HiringFunnel = ({ data }: any) => {
    const chartData = [
        { stage: 'Applied', count: data.applied, fill: '#0066FF' },
        { stage: 'Screening', count: data.screening, fill: '#6366f1' },
        { stage: 'Interview', count: data.interview, fill: '#a855f7' },
        { stage: 'Offer', count: data.offer, fill: '#ec4899' },
        { stage: 'Hired', count: data.hired, fill: '#10b981' },
    ];

    return (
        <div className="bg-white border border-gray-100 rounded-[56px] p-10 shadow-sm space-y-8">
            <div className="flex items-center justify-between">
                <div>
                     <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tighter">Hiring Pipeline</h3>
                     <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 italic">Conversion dynamics across all active sectors</p>
                </div>
            </div>
            <div className="h-[250px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
                         <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                         <XAxis 
                            dataKey="stage" 
                            axisLine={false} 
                            tickLine={false} 
                            tick={{ fontSize: 10, fontWeight: 900, fill: '#9ca3af', textAnchor: 'middle' }}
                         />
                         <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 900, fill: '#9ca3af' }} />
                         <Tooltip 
                            cursor={{ fill: 'rgba(0,0,0,0.02)' }}
                            contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', fontSize: '12px', fontWeight: 900, fontStyle: 'italic' }}
                         />
                         <Bar dataKey="count" radius={[12, 12, 0, 0]} barSize={40}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.fill} />
                            ))}
                         </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

// --- CANDIDATE RECOMMENDED JOBS ---
export const RecommendedJobs = ({ jobs }: any) => (
    <div className="bg-white border border-gray-100 rounded-[56px] p-10 shadow-sm space-y-8">
        <div className="flex items-center justify-between">
            <div>
                 <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tighter">AI Match Spectrum</h3>
                 <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 italic">Top-tier recommendations predicted by HireSight Neural Engine</p>
            </div>
            <Link href="/jobs" className="p-3 bg-gray-50 border border-gray-100 rounded-2xl hover:bg-zinc-900 hover:text-white transition-all group">
                <ChevronRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
        </div>
        <div className="space-y-4">
            {jobs.map((job: any, i: number) => (
                <div key={job.id} className="p-4 border border-gray-50 rounded-[28px] hover:bg-gray-50/50 transition-all flex items-center justify-between group cursor-pointer">
                    <div className="flex items-center space-x-6">
                        <div className="w-14 h-14 bg-white border border-gray-100 rounded-2xl flex items-center justify-center font-black text-zinc-300 text-xl overflow-hidden group-hover:scale-105 transition-transform">
                            {job.company?.avatar_url ? <img src={job.company.avatar_url} className="w-full h-full object-cover" /> : job.company?.company_name?.[0] || 'C'}
                        </div>
                        <div>
                             <h4 className="font-black text-zinc-900 italic tracking-tight">{job.title}</h4>
                             <div className="flex items-center space-x-3 text-[10px] font-bold text-gray-400 mt-1">
                                 <span className="flex items-center"><MapPin className="w-3 h-3 mr-1" /> {job.location}</span>
                                 <span className="w-1 h-1 bg-gray-200 rounded-full" />
                                 <span className="text-primary italic">{job.company?.company_name || 'Matrix Corp'}</span>
                             </div>
                        </div>
                    </div>
                    <div className="flex flex-col items-end space-y-1">
                        <div className="text-lg font-black text-primary italic leading-none group-hover:scale-110 transition-transform">98%</div>
                        <span className="text-[8px] font-black text-gray-300 uppercase tracking-widest">Stability Match</span>
                    </div>
                </div>
            ))}
        </div>
    </div>
);

// --- INTERVIEW CALENDAR QUICK VIEW ---
export const InterviewCalendar = ({ interviews }: any) => (
    <div className="bg-zinc-900 text-white rounded-[48px] p-10 shadow-2xl space-y-8 relative overflow-hidden">
        <div className="flex items-center justify-between relative z-10">
            <h3 className="text-xl font-black font-display italic tracking-tight">Sync Agenda</h3>
            <div className="p-3 bg-white/10 rounded-2xl text-primary border border-white/5">
                <Calendar className="w-5 h-5" />
            </div>
        </div>
        
        <div className="space-y-6 relative z-10">
            {interviews && interviews.length > 0 ? interviews.map((iv: any) => (
                <div key={iv.id} className="flex space-x-5 group">
                    <div className="flex flex-col items-center">
                        <div className="text-xs font-black italic text-primary">{new Date(iv.start_time).toLocaleDateString('en-US', { day: '2-digit' })}</div>
                        <div className="text-[8px] font-black uppercase text-gray-500">{new Date(iv.start_time).toLocaleDateString('en-US', { month: 'short' })}</div>
                    </div>
                    <div className="flex-1 pb-6 border-b border-white/5">
                        <h5 className="text-sm font-black italic tracking-tight group-hover:text-primary transition-colors">{iv.job?.title}</h5>
                        <p className="text-[10px] font-bold text-gray-400 mt-1 uppercase tracking-widest">{new Date(iv.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {iv.type}</p>
                    </div>
                </div>
            )) : (
                <div className="py-8 text-center bg-white/5 rounded-3xl border border-dashed border-white/10">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] italic">No Neural Syncs Linked</p>
                </div>
            )}
        </div>

        <div className="absolute right-0 bottom-0 w-32 h-32 bg-primary/20 blur-[80px] rounded-full translate-x-1/2 translate-y-1/2" />
    </div>
);
