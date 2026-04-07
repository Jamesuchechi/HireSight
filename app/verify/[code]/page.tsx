"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    ShieldCheck, Trophy, Target, 
    Clock, CheckCircle2, XCircle,
    BrainCircuit, Info, ExternalLink,
    AlertCircle, Activity
} from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";

export default function VerificationHub({ params }: { params: Promise<{ code: string }> }) {
    const { code } = use(params);
    const supabase = createClient();
    
    const [badge, setBadge] = useState<any>(null);
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const verifyNode = async () => {
            // 1. Fetch Badge by Verification Code (Public)
            const { data: bData, error } = await supabase
                .from("skill_badges")
                .select("*, profiles(full_name, id)")
                .eq("verification_code", code)
                .single();

            if (error || !bData) {
                console.error("Verification Signal Lost:", error);
                setLoading(false);
                return;
            }

            setBadge(bData);
            setProfile(bData.profiles);
            setLoading(false);
        };

        verifyNode();
    }, [code, supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-screen bg-gray-50">
             <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!badge) return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 text-center p-6 space-y-8">
             <div className="p-8 bg-red-100 text-red-500 rounded-full animate-pulse">
                 <AlertCircle className="w-16 h-16" />
             </div>
             <div className="space-y-4">
                <h1 className="text-4xl font-black italic uppercase tracking-tighter">Verification Unsuccessful</h1>
                <p className="text-gray-500 font-bold max-w-sm mx-auto italic">The provided neural code could not be indexed in the HireSight matrix. This credential may be invalid or expired.</p>
             </div>
             <Link href="/" className="px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black uppercase text-xs italic shadow-xl">Return to Hub</Link>
        </div>
    );

    const levelColors: Record<string, string> = {
        bronze: "from-amber-600 to-amber-700",
        silver: "from-gray-400 to-gray-500",
        gold: "from-yellow-400 to-yellow-600",
        platinum: "from-cyan-400 to-cyan-600 text-white"
    };

    const isPlatinum = badge.badge_level === 'platinum';

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4 md:p-12 selection:bg-primary/20 selection:text-primary">
            <div className="max-w-4xl w-full space-y-12">
                {/* Status Card */}
                <div className="bg-white rounded-[64px] shadow-2xl overflow-hidden border border-gray-100 flex flex-col md:flex-row items-stretch">
                     {/* Badge Visualization */}
                     <div className={`p-12 md:p-20 bg-gradient-to-br ${levelColors[badge.badge_level] || levelColors.bronze} flex flex-col items-center justify-center space-y-8 text-white relative overflow-hidden md:w-1/3`}>
                        <div className="relative z-10 w-32 h-32 bg-white/20 backdrop-blur-xl border-4 border-white/40 rounded-[32px] flex items-center justify-center shadow-2xl animate-pulse">
                             <Trophy className="w-16 h-16" />
                        </div>
                        <div className="relative z-10 text-center">
                            <h2 className="text-4xl font-black italic leading-none">{badge.badge_level.toUpperCase()}</h2>
                            <p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 mt-2">Neural Node Status</p>
                        </div>
                        {/* Aesthetic */}
                        <div className="absolute right-0 bottom-0 w-32 h-32 bg-white/5 blur-[40px] rounded-full translate-x-1/2 translate-y-1/2" />
                     </div>

                     {/* Verification Details */}
                     <div className="p-10 md:p-20 flex-1 space-y-10">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3 text-emerald-500">
                                 <ShieldCheck className="w-6 h-6" />
                                 <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">Credential Verified</span>
                            </div>
                            <div className="text-[8px] font-black text-gray-300 uppercase tracking-widest hidden sm:block">ID: HS-PRISM-V2</div>
                        </div>

                        <div className="space-y-4">
                            <h1 className="text-3xl md:text-5xl font-black italic tracking-tighter text-zinc-900 leading-none">
                                {profile?.full_name?.toUpperCase()}
                            </h1>
                            <div className="flex flex-wrap items-center gap-4 text-[10px] font-black text-gray-400 uppercase tracking-widest italic">
                                <span>Technical Expert</span>
                                <span className="text-gray-200">|</span>
                                <span>Node: {badge.skill_name}</span>
                                <span className="text-gray-200">|</span>
                                <span>Vetted: {new Date(badge.issued_at).toLocaleDateString()}</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-gray-100">
                            <div className="space-y-2">
                                <div className="flex items-center space-x-2 text-primary">
                                     <Activity className="w-4 h-4" />
                                     <span className="text-[8px] font-black uppercase tracking-widest">Neural Index</span>
                                </div>
                                <div className="text-4xl font-black italic text-zinc-900 leading-none">{badge.score}%</div>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center space-x-2 text-primary">
                                     <BrainCircuit className="w-4 h-4" />
                                     <span className="text-[8px] font-black uppercase tracking-widest">Verification Code</span>
                                </div>
                                <div className="text-lg font-black italic text-zinc-900 tracking-widest">{badge.verification_code}</div>
                            </div>
                        </div>

                        <div className="pt-10 flex flex-col sm:flex-row items-center gap-6">
                             <div className="flex-grow p-6 bg-gray-50 rounded-[32px] flex items-center space-x-4 border border-gray-100">
                                 <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center text-primary shadow-sm">
                                     <Info className="w-6 h-6" />
                                 </div>
                                 <p className="text-[10px] font-bold text-gray-500 italic flex-1">
                                    This credential is tamper-proof and hosted on the HireSight V2.0 Neural Matrix. 
                                 </p>
                             </div>
                             <Link href="/" className="px-10 py-5 bg-zinc-900 text-white rounded-3xl font-black italic text-xs uppercase tracking-widest hover:scale-105 transition-all shadow-xl">
                                Visit Platform
                             </Link>
                        </div>
                     </div>
                </div>

                {/* Footer Brand */}
                <div className="text-center space-y-4">
                     <p className="text-[10px] font-black text-gray-400 uppercase tracking-[0.4em] italic">Vetted via HireSight AI Matrix</p>
                     <img src="/logo.png" alt="HireSight" className="h-8 mx-auto grayscale opacity-20" />
                </div>
            </div>
        </div>
    );
}
