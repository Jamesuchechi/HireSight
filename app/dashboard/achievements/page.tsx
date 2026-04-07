"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Trophy, ShieldCheck, Share2, 
    Download, ExternalLink, Filter,
    CheckCircle2, Star, Calendar, Clock,
    Layers, BrainCircuit, ArrowRight, RotateCcw
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { downloadCertificate } from "@/lib/utils/certificate";

export default function NeuralTrophyCase() {
    const supabase = createClient();
    const [badges, setBadges] = useState<any[]>([]);
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchBadges = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data: pData } = await supabase.from("profiles").select("full_name").eq("id", user.id).single();
            if (pData) setProfile(pData);

            const { data } = await supabase
                .from("skill_badges")
                .select(`
                    *,
                    assessment:assessments(title, category)
                `)
                .eq("user_id", user.id)
                .order("issued_at", { ascending: false });

            if (data) setBadges(data);
            setLoading(false);
        };

        fetchBadges();
    }, [supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-32">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                <div className="space-y-4">
                    <div className="flex items-center space-x-3 text-primary">
                         <Trophy className="w-6 h-6" />
                         <span className="text-[10px] font-black uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">Archived Achievements</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Neural <span className="text-primary tracking-normal">Trophy Case</span>
                    </h1>
                    <p className="text-gray-500 font-bold max-w-lg">Your collection of verifiable technical milestones and neural-verified skill badges.</p>
                </div>
            </header>

            {/* Badges Grid */}
            {badges.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {badges.map((badge) => (
                        <BadgeCard key={badge.id} badge={badge} fullName={profile?.full_name || "HireSight User"} />
                    ))}
                </div>
            ) : (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[56px] p-24 text-center space-y-8">
                    <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-300">
                        <Trophy className="w-12 h-12" />
                    </div>
                    <div className="space-y-4">
                        <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight uppercase leading-none">Matrix Empty</h3>
                        <p className="text-gray-500 font-bold max-w-sm mx-auto italic">No neural badges have been archived yet. Initiate a vetting mission to verify your skills.</p>
                        <Link 
                            href="/dashboard/assessments/browse"
                            className="inline-flex px-10 py-4 bg-zinc-900 text-white rounded-[24px] font-black text-[10px] uppercase tracking-widest italic hover:scale-105 transition-all shadow-xl shadow-zinc-900/10"
                        >
                            Explore Missions
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
}

function BadgeCard({ badge, fullName }: { badge: any, fullName: string }) {
    const [isDownloading, setIsDownloading] = useState(false);

    const handleShare = () => {
        const verifyUrl = `${window.location.origin}/verify/${badge.verification_code}`;
        navigator.clipboard.writeText(verifyUrl);
        alert("Verification Link Copied to Clipboard Node");
    };

    const handleDownload = async () => {
        setIsDownloading(true);
        try {
            await downloadCertificate(badge, fullName);
        } finally {
            setIsDownloading(false);
        }
    };

    const levelColors: Record<string, string> = {
        bronze: "text-amber-700 bg-amber-50 border-amber-200 shadow-amber-500/10",
        silver: "text-gray-500 bg-gray-50 border-gray-200 shadow-gray-500/10",
        gold: "text-yellow-600 bg-yellow-50 border-yellow-200 shadow-yellow-500/10",
        platinum: "text-cyan-600 bg-cyan-50 border-cyan-200 shadow-cyan-500/10"
    };

    const colorClass = levelColors[badge.badge_level] || levelColors.bronze;

    return (
        <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`group bg-white border rounded-[56px] p-10 shadow-xl overflow-hidden relative ${colorClass.split(' ').slice(2).join(' ')}`}
        >
            <div className="relative z-10 space-y-8 text-center flex flex-col items-center">
                <div className={`w-24 h-24 rounded-[32px] border-4 flex items-center justify-center transition-all group-hover:scale-110 shadow-2xl bg-white ${colorClass.split(' ').slice(0, 2).join(' ')}`}>
                    <Star className={`w-12 h-12 ${badge.badge_level === 'gold' ? 'fill-current' : ''}`} />
                </div>

                <div className="space-y-2">
                    <span className={`px-4 py-1.5 rounded-xl text-[8px] font-black uppercase tracking-widest italic ${colorClass.split(' ').slice(0, 2).join(' ')}`}>
                        {badge.badge_level} Node
                    </span>
                    <h3 className="text-3xl font-black text-zinc-900 italic tracking-tighter leading-tight">{badge.skill_name}</h3>
                    <p className="text-[10px] font-bold text-gray-400 italic">{badge.assessment?.title}</p>
                </div>

                <div className="grid grid-cols-2 gap-4 w-full">
                    <div className="bg-gray-50/50 p-4 rounded-3xl space-y-1">
                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic">Neural Score</p>
                        <p className="text-lg font-black text-zinc-900 italic">{badge.score}%</p>
                    </div>
                    <div className="bg-gray-50/50 p-4 rounded-3xl space-y-1">
                        <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic">Archived</p>
                        <p className="text-lg font-black text-zinc-900 italic">{formatDistanceToNow(new Date(badge.issued_at))} ago</p>
                    </div>
                </div>

                <div className="w-full flex items-center space-x-2 bg-zinc-900 p-4 rounded-3xl group-hover:bg-primary transition-all">
                    <div className="text-left flex-1 min-w-0">
                        <p className="text-[8px] font-black text-white/40 uppercase tracking-widest mb-1">Verify Node</p>
                        <p className="text-xs font-black text-white tracking-widest truncate">{badge.verification_code}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                        <button 
                            onClick={handleShare}
                            className="p-3 bg-white/10 text-white rounded-xl hover:bg-white/20 transition-all"
                            title="Copy Verification Link"
                        >
                             <Share2 className="w-4 h-4" />
                        </button>
                        <button 
                            onClick={handleDownload}
                            disabled={isDownloading}
                            className="p-3 bg-white/10 text-white rounded-xl hover:bg-white/20 transition-all disabled:opacity-50"
                            title="Download Certificate"
                        >
                             {isDownloading ? (
                                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                             ) : (
                                <Download className="w-4 h-4" />
                             )}
                        </button>
                    </div>
                </div>

                <div className="w-full flex flex-col sm:flex-row items-center gap-3">
                     <Link 
                        href={`/dashboard/assessments/results/${badge.attempt_id}`}
                        className="w-full sm:flex-1 py-4 px-6 bg-zinc-900 text-white rounded-3xl text-[10px] font-black uppercase tracking-widest italic hover:bg-primary transition-all flex items-center justify-center space-x-2"
                     >
                        <span>Review Analysis</span>
                        <ArrowRight className="w-4 h-4" />
                     </Link>
                     <Link 
                        href={`/dashboard/assessments/${badge.assessment_id}/take`}
                        className="w-full sm:flex-1 py-4 px-6 border border-zinc-200 text-zinc-900 rounded-3xl text-[10px] font-black uppercase tracking-widest italic hover:bg-gray-50 transition-all flex items-center justify-center space-x-2"
                     >
                        <span>Retake Mission</span>
                        <RotateCcw className="w-4 h-4" />
                     </Link>
                </div>
            </div>

            <div className="absolute right-0 bottom-0 w-64 h-64 bg-primary/5 blur-[100px] rounded-full translate-x-1/2 translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity" />
        </motion.div>
    );
}
