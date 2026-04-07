"use client";

import { useState, useEffect } from "react";
import { 
    Users, CheckCircle2, XCircle, 
    MessageSquare, ShieldCheck, Zap,
    ArrowUpRight, BarChart3, Fingerprint,
    Scale
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";

interface Vote {
    id: string;
    voter_name: string;
    voter_role: string;
    decision: 'hire' | 'reject' | 'discuss';
    confidence: number;
    notes: string;
}

export default function ConsensusHub({ applicationId }: { applicationId: string }) {
    const supabase = createClient();
    const [votes, setVotes] = useState<Vote[]>([]);
    const [myVote, setMyVote] = useState<Partial<Vote> | null>(null);
    const [isBlind, setIsBlind] = useState(true);
    const [loading, setLoading] = useState(true);

    const MOCK_VOTES: Vote[] = [
        { id: '1', voter_name: 'Sarah Chen', voter_role: 'Tech Lead', decision: 'hire', confidence: 90, notes: 'Extreme technical depth in distributed systems.' },
        { id: '2', voter_name: 'Marcus Thorne', voter_role: 'Director', decision: 'discuss', confidence: 60, notes: 'Concerned about cultural alignment with the stealth team.' }
    ];

    useEffect(() => {
        // In reality, subscribe to database changes for real-time consensus
        setTimeout(() => {
            setVotes(MOCK_VOTES);
            setLoading(false);
        }, 800);
    }, [applicationId]);

    const handleVote = (decision: 'hire' | 'reject' | 'discuss') => {
        setMyVote({ decision, confidence: 80 });
        // After voting, reveal all votes
        setIsBlind(false);
    };

    return (
        <div className="bg-zinc-950 border border-white/5 rounded-[48px] p-12 overflow-hidden relative min-h-[600px]">
            {/* Background Atmosphere */}
            <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 blur-[100px] rounded-full translate-x-1/2 -translate-y-1/2" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/5 blur-[80px] rounded-full -translate-x-1/2 translate-y-1/2" />

            <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* Left: Summary & Decision Matrix */}
                <div className="lg:col-span-4 space-y-10">
                    <header className="space-y-4">
                        <div className="flex items-center space-x-3">
                             <div className="p-2 bg-primary/10 rounded-xl">
                                 <Users className="w-5 h-5 text-primary" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic leading-none">Command Consensus Hub</span>
                        </div>
                        <h2 className="text-4xl font-black text-white italic tracking-tighter uppercase leading-none">Decision <span className="text-primary italic">Matrix</span></h2>
                        <p className="text-xs font-bold text-gray-500 italic leading-relaxed">
                            Final synchronization for Candidate ID: {applicationId.substring(0, 8)}. 
                            All votes are blind until personal assessment is committed.
                        </p>
                    </header>

                    <div className="space-y-6">
                        <div className="p-8 bg-white/5 rounded-[32px] border border-white/10 space-y-4">
                             <div className="flex items-center justify-between">
                                 <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Agreement Pulse</h4>
                                 <Scale className="w-4 h-4 text-emerald-500" />
                             </div>
                             <div className="flex items-end space-x-2">
                                 <span className="text-4xl font-black text-white italic tracking-tighter">67%</span>
                                 <span className="text-[10px] font-black text-emerald-500 uppercase italic mb-1">Divergence Detected</span>
                             </div>
                             <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                 <div className="h-full bg-emerald-500 w-[67%]" />
                             </div>
                        </div>

                        {!myVote ? (
                            <div className="p-8 bg-primary/10 rounded-[40px] border border-primary/20 space-y-6">
                                <h4 className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic text-center">Commit Your Decision</h4>
                                <div className="grid grid-cols-1 gap-3">
                                    <VoteButton icon={<CheckCircle2 className="w-4 h-4" />} label="Hire Asset" color="bg-emerald-500" onClick={() => handleVote('hire')} />
                                    <VoteButton icon={<MessageSquare className="w-4 h-4" />} label="Needs Debrief" color="bg-zinc-800" onClick={() => handleVote('discuss')} />
                                    <VoteButton icon={<XCircle className="w-4 h-4" />} label="Abort mission" color="bg-red-500" onClick={() => handleVote('reject')} />
                                </div>
                            </div>
                        ) : (
                            <div className="p-8 bg-zinc-900 rounded-[40px] border border-white/10 text-center animate-in fade-in zoom-in">
                                <ShieldCheck className="w-12 h-12 text-primary mx-auto mb-4" />
                                <h4 className="text-xl font-black text-white italic tracking-tight uppercase">Assessment Logged</h4>
                                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic mt-2">Personal blinders removed.</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Real-time Feed */}
                <div className="lg:col-span-8 space-y-8">
                    <div className="flex items-center justify-between">
                         <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Team Assessments</h5>
                         <div className="flex items-center space-x-2 px-3 py-1 bg-white/5 rounded-full border border-white/10">
                              <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                              <span className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic">Live Sync Active</span>
                         </div>
                    </div>

                    <div className="space-y-4">
                        <AnimatePresence mode="popLayout">
                            {votes.map((vote, idx) => (
                                <motion.div
                                    key={vote.id}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: idx * 0.1 }}
                                    className="p-8 bg-zinc-900/50 rounded-[32px] border border-white/5 relative group hover:border-primary/20 transition-all"
                                >
                                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                                        <div className="flex items-center space-x-4">
                                             <div className="w-12 h-12 rounded-2xl bg-white/5 flex items-center justify-center border border-white/10">
                                                 <Fingerprint className="w-6 h-6 text-gray-500 group-hover:text-primary transition-colors" />
                                             </div>
                                             <div>
                                                 <h5 className="text-lg font-black text-white italic tracking-tight uppercase leading-none">{vote.voter_name}</h5>
                                                 <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] italic mt-1">{vote.voter_role}</p>
                                             </div>
                                        </div>

                                        <div className="flex items-center space-x-6">
                                             <div className="text-right">
                                                 <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1 italic">Decision</p>
                                                 {isBlind ? (
                                                     <div className="px-4 py-1.5 bg-zinc-800 rounded-lg blur-[4px] select-none">*******</div>
                                                 ) : (
                                                     <div className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest italic ${
                                                         vote.decision === 'hire' ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20' :
                                                         vote.decision === 'reject' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                                                         'bg-zinc-800 text-gray-400 border border-white/5'
                                                     }`}>
                                                         {vote.decision === 'hire' ? 'HIRE ASSET' : vote.decision === 'reject' ? 'ABORT MISSION' : 'REQUIRES DEBRIEF'}
                                                     </div>
                                                 )}
                                             </div>
                                             
                                             <div className="w-12 h-12 rounded-full border-4 border-white/5 flex items-center justify-center relative">
                                                 {isBlind ? (
                                                      <Zap className="w-4 h-4 text-gray-700" />
                                                 ) : (
                                                     <>
                                                         <svg className="w-full h-full -rotate-90">
                                                            <circle cx="24" cy="24" r="20" fill="transparent" stroke="currentColor" strokeWidth="4" className="text-white/5" />
                                                            <circle cx="24" cy="24" r="20" fill="transparent" stroke="currentColor" strokeWidth="4" strokeDasharray={`${vote.confidence * 1.25} 125`} className="text-primary" />
                                                         </svg>
                                                         <span className="absolute text-[8px] font-black text-white italic">{vote.confidence}%</span>
                                                     </>
                                                 )}
                                             </div>
                                        </div>
                                    </div>

                                    {!isBlind && (
                                        <motion.div 
                                            initial={{ height: 0, opacity: 0 }}
                                            animate={{ height: "auto", opacity: 1 }}
                                            className="mt-6 pt-6 border-t border-white/5"
                                        >
                                            <p className="text-sm font-bold text-gray-400 italic leading-relaxed">
                                                "{vote.notes}"
                                            </p>
                                        </motion.div>
                                    )}
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );
}

function VoteButton({ icon, label, color, onClick }: any) {
    return (
        <button 
            onClick={onClick}
            className={`w-full p-4 rounded-2xl flex items-center justify-between group transition-all hover:scale-[1.02] ${color} text-white shadow-xl`}
        >
            <div className="flex items-center space-x-4">
                <div className="p-2 bg-black/20 rounded-xl group-hover:scale-110 transition-transform">
                    {icon}
                </div>
                <span className="text-[10px] font-black uppercase tracking-widest italic">{label}</span>
            </div>
            <ArrowUpRight className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
        </button>
    );
}
