"use client";

import { 
    CheckCircle2, 
    AlertCircle, 
    ArrowUpRight, 
    Zap, 
    Target, 
    Activity 
} from "lucide-react";
import { motion } from "framer-motion";

interface AuditPanelProps {
    score: number;
    metrics: {
        impact: number;
        verbs: number;
        keywords: number;
    };
    suggestions: Array<{
        category: string;
        title: string;
        description: string;
    }>;
}

export default function AuditPanel({ score, metrics, suggestions }: AuditPanelProps) {
    return (
        <div className="space-y-8 sticky top-8">
            {/* Main Score Card */}
            <div className="bg-zinc-900 rounded-[40px] p-10 text-white relative overflow-hidden shadow-2xl">
                <div className="relative z-10">
                    <div className="flex items-center justify-between mb-8">
                        <div className="p-3 bg-white/10 rounded-2xl backdrop-blur-md">
                            <Target className="w-5 h-5 text-primary" />
                        </div>
                        <span className="text-[10px] font-black uppercase tracking-[0.3em] text-white/40">DNA Resonance</span>
                    </div>
                    
                    <div className="flex items-end space-x-2 mb-2">
                        <span className="text-7xl font-black font-display italic leading-none">{score}</span>
                        <span className="text-2xl font-black font-display italic text-primary mb-1">%</span>
                    </div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-white/60 mb-8">Structural Integrity Score</p>
                    
                    <div className="w-full bg-white/10 h-2 rounded-full overflow-hidden">
                        <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${score}%` }}
                            className="bg-primary h-full rounded-full"
                        />
                    </div>
                </div>
                
                {/* Decoration */}
                <div className="absolute top-[-50px] right-[-50px] w-64 h-64 bg-primary/20 blur-[100px] rounded-full" />
            </div>

            {/* Metric Grid */}
            <div className="grid grid-cols-1 gap-4">
                {[
                    { label: "Impact Factor", value: metrics.impact, icon: <Activity className="w-4 h-4" /> },
                    { label: "Action Verbs", value: metrics.verbs, icon: <Zap className="w-4 h-4" /> },
                    { label: "Keyword Density", value: metrics.keywords, icon: <Target className="w-4 h-4" /> },
                ].map((m, idx) => (
                    <div key={idx} className="bg-white border border-gray-100 rounded-[28px] p-6 flex items-center justify-between hover:border-primary/20 transition-all group">
                        <div className="flex items-center space-x-4">
                            <div className="p-3 bg-gray-50 text-gray-400 rounded-xl group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                                {m.icon}
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-400 group-hover:text-zinc-900 transition-colors">{m.label}</span>
                        </div>
                        <span className="text-xl font-black font-display italic">{m.value}%</span>
                    </div>
                ))}
            </div>

            {/* Suggestions Feed */}
            <div className="space-y-4">
                <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-400 ml-4 mb-6">AI Tactical Advisories</h4>
                {suggestions.map((s, idx) => (
                    <motion.div 
                        key={idx}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm hover:shadow-lg transition-all relative group"
                    >
                        <div className="flex items-start space-x-4">
                            <div className={`p-2 rounded-lg mt-1 ${idx % 2 === 0 ? "bg-amber-50 text-amber-500" : "bg-blue-50 text-blue-500"}`}>
                                {idx % 2 === 0 ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
                            </div>
                            <div className="space-y-1 pr-6">
                                <h5 className="text-[10px] font-black uppercase tracking-widest text-zinc-900 leading-tight pr-4">{s.title}</h5>
                                <p className="text-[11px] text-gray-500 font-medium leading-relaxed">{s.description}</p>
                            </div>
                        </div>
                        <ArrowUpRight className="absolute top-6 right-6 w-4 h-4 text-gray-200 group-hover:text-primary transition-colors" />
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
