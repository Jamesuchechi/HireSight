"use client";

import { motion, AnimatePresence } from "framer-motion";
import { BrainCircuit, Star, Zap, Activity } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface IntelligenceTickerProps {
    logs: any[];
}

export default function IntelligenceTicker({ logs }: IntelligenceTickerProps) {
    return (
        <div className="bg-zinc-900/50 rounded-[40px] border border-white/5 p-8 relative overflow-hidden">
            <header className="flex items-center justify-between mb-8">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                        <Activity className="w-4 h-4 text-primary" />
                    </div>
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] italic">Neural Log Feed</span>
                </div>
                <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest italic leading-none">Live Sync</span>
                </div>
            </header>

            <div className="space-y-4 max-h-[500px] overflow-y-auto pr-4 custom-scrollbar">
                <AnimatePresence mode="popLayout">
                    {logs.map((log, idx) => (
                        <motion.div
                            key={log.id || idx}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="p-5 bg-white/5 rounded-3xl border border-white/5 hover:bg-white/10 transition-colors group cursor-default"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex items-center space-x-2">
                                    <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${
                                        log.type === 'assessment' ? 'bg-primary/20 text-primary' : 'bg-indigo-500/20 text-indigo-400'
                                    }`}>
                                        {log.type === 'assessment' ? <Star className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
                                    </div>
                                    <div>
                                        <p className="text-[9px] font-black text-gray-400 uppercase tracking-widest leading-none mb-1 italic">
                                            {log.protocol === 'training' ? 'Training Mission' : 'Live Protocol'}
                                        </p>
                                        <p className="text-sm font-black text-white italic truncate max-w-[150px]">
                                            {log.candidate_name}
                                        </p>
                                    </div>
                                </div>
                                <span className="text-[8px] font-bold text-gray-600 uppercase italic">
                                    {formatDistanceToNow(new Date(log.created_at || new Date()))} ago
                                </span>
                            </div>
                            
                            <p className="text-xs font-bold text-gray-400 italic leading-relaxed line-clamp-2 group-hover:line-clamp-none transition-all">
                                {log.message}
                            </p>

                            {log.score && (
                                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                                    <div className="flex items-center space-x-1">
                                        {[1,2,3,4,5].map(i => (
                                            <Star key={i} className={`w-2.5 h-2.5 ${i <= log.score ? 'text-primary' : 'text-gray-700'}`} />
                                        ))}
                                    </div>
                                    <span className="text-[10px] font-black text-primary italic uppercase tracking-widest">
                                        Score: {log.score * 20}%
                                    </span>
                                </div>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-zinc-900 via-zinc-900/50 to-transparent pointer-events-none" />
        </div>
    );
}
