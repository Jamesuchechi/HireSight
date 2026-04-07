"use client";

import { motion } from "framer-motion";
import { 
    Award, BrainCircuit, Target, 
    Star, MessageSquare, ShieldCheck,
    TrendingUp, Cpu, Zap, ArrowRight,
    CheckCircle2, AlertCircle
} from "lucide-react";

interface ReportProps {
    report: {
        overall_score: number;
        star_assessment: {
            situation: string;
            task: string;
            action: string;
            result: string;
        };
        technical_feedback: string;
        behavioral_feedback: string;
        suggested_next_steps: string;
    };
    interviewType: string;
}

export default function InterviewReport({ report, interviewType }: ReportProps) {
    if (!report) return (
        <div className="p-12 text-center bg-white border border-gray-100 rounded-[48px] space-y-4 shadow-sm">
             <Loader2 className="w-8 h-8 text-primary animate-spin mx-auto" />
             <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Awaiting AI Synchronization...</p>
        </div>
    );

    return (
        <div className="space-y-12">
            {/* Mission Performance Matrix */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="md:col-span-2 bg-zinc-900 rounded-[48px] p-12 relative overflow-hidden group shadow-2xl"
                >
                    <div className="relative z-10 space-y-8">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-primary/10 text-primary rounded-2xl border border-primary/20">
                                <Award className="w-6 h-6" />
                            </div>
                            <div>
                                <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic mb-1">Performance Core</h4>
                                <h3 className="text-3xl font-black text-white italic tracking-tighter uppercase leading-none">Mission Debrief</h3>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-8">
                             <div className="space-y-2">
                                 <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest italic ml-2">Intelligence Score</p>
                                 <div className="flex items-baseline space-x-2">
                                     <span className="text-6xl font-black text-white italic tracking-tighter tabular-nums leading-none">{report.overall_score || 0}</span>
                                     <span className="text-xl font-black text-primary italic">/ 100</span>
                                 </div>
                             </div>
                             <div className="space-y-2">
                                 <p className="text-[9px] font-black text-gray-500 uppercase tracking-widest italic ml-2">Assessment Type</p>
                                 <div className="px-6 py-4 bg-white/5 rounded-3xl border border-white/10 flex items-center space-x-3">
                                     <Target className="w-5 h-5 text-primary" />
                                     <span className="text-sm font-black text-white uppercase italic tracking-widest">{interviewType} Scan</span>
                                 </div>
                             </div>
                        </div>

                        <div className="pt-8 border-t border-white/10 space-y-4">
                             <div className="flex items-center justify-between px-2">
                                 <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Neural Efficiency</span>
                                 <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest italic">Target Optimised</span>
                             </div>
                             <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                 <motion.div 
                                    initial={{ width: 0 }}
                                    animate={{ width: `${report.overall_score || 0}%` }}
                                    className="h-full bg-primary shadow-[0_0_20px_rgba(0,102,255,0.8)]"
                                 />
                             </div>
                        </div>
                    </div>
                </motion.div>

                <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm flex flex-col justify-between"
                >
                    <div className="space-y-6">
                        <div className="p-3 w-fit bg-emerald-500/10 text-emerald-600 rounded-2xl">
                            <TrendingUp className="w-6 h-6" />
                        </div>
                        <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic mb-2">Next Phase Directives</h4>
                        <p className="text-sm font-bold text-zinc-900 italic leading-relaxed">
                            "{report.suggested_next_steps || 'Awaiting additional training vectors...'}"
                        </p>
                    </div>
                    <button className="w-full py-5 bg-zinc-900 text-white rounded-3xl font-black text-[10px] uppercase tracking-widest italic hover:bg-primary transition-all flex items-center justify-center space-x-2 group mt-8">
                        <span>Advance to Selection</span>
                        <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </button>
                </motion.div>
            </div>

            {/* STAR Assessment Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StarCard title="Situation" content={report.star_assessment?.situation} color="primary" delay={0.1} />
                <StarCard title="Task" content={report.star_assessment?.task} color="amber" delay={0.2} />
                <StarCard title="Action" content={report.star_assessment?.action} color="emerald" delay={0.3} />
                <StarCard title="Result" content={report.star_assessment?.result} color="indigo" delay={0.4} />
            </div>

            {/* Intelligence Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <FeedbackCard 
                    title="Technical Audit" 
                    content={report.technical_feedback} 
                    icon={<Cpu className="w-5 h-5" />} 
                    color="primary"
                />
                <FeedbackCard 
                    title="Behavioral Scan" 
                    content={report.behavioral_feedback} 
                    icon={<Zap className="w-5 h-5" />} 
                    color="amber"
                />
            </div>
        </div>
    );
}

function StarCard({ title, content, color, delay }: any) {
    const colors: any = {
        primary: "text-primary border-primary/20 bg-primary/5",
        amber: "text-amber-500 border-amber-500/20 bg-amber-500/5",
        emerald: "text-emerald-500 border-emerald-500/20 bg-emerald-500/5",
        indigo: "text-indigo-500 border-indigo-500/20 bg-indigo-500/5"
    };

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay }}
            className={`p-8 rounded-[40px] border-2 ${colors[color]} space-y-4`}
        >
            <h5 className="text-[10px] font-black uppercase tracking-[0.3em] font-display italic underline decoration-2 decoration-current/20">{title}</h5>
            <p className="text-xs font-bold italic leading-relaxed text-zinc-900 line-clamp-6 group-hover:line-clamp-none transition-all">
                {content || "No tactical data recorded."}
            </p>
        </motion.div>
    );
}

function FeedbackCard({ title, content, icon, color }: any) {
    return (
        <div className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm space-y-8">
            <div className="flex items-center space-x-4">
                 <div className={`p-4 rounded-2xl ${color === 'primary' ? 'bg-primary/10 text-primary' : 'bg-amber-500/10 text-amber-600'}`}>
                     {icon}
                 </div>
                 <h4 className="text-xl font-black italic text-zinc-900 uppercase tracking-tighter">{title}</h4>
            </div>
            <div className="prose prose-zinc max-w-none">
                <p className="text-sm text-gray-600 font-bold italic leading-relaxed bg-gray-50 p-8 rounded-[40px] border border-gray-100">
                    {content || "Neural scan in progress..."}
                </p>
            </div>
        </div>
    );
}

function Loader2({ className }: { className?: string }) {
    return <div className={`border-4 border-primary border-t-transparent rounded-full animate-spin ${className}`} />;
}
