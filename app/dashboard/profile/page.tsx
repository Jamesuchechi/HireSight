"use client";

import { useEffect, useState } from "react";
import { 
    MapPin, 
    Calendar, 
    Link as LinkIcon, 
    Edit3, 
    Briefcase, 
    Zap, 
    FileText, 
    Star, 
    MoreHorizontal,
    ArrowLeft
} from "lucide-react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function ProfilePage() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProfile = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            const { data: profile } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            if (profile) {
                setProfile(profile);
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase, router]);

    if (loading) return null;

    const isRecruiter = profile?.role === "recruiter";

    return (
        <div className="max-w-5xl mx-auto pb-20">
            {/* Header / Nav */}
            <div className="flex items-center space-x-8 px-4 py-2 mb-2 sticky top-0 bg-white/80 backdrop-blur-md z-20">
                <button 
                    onClick={() => router.back()}
                    className="p-2 hover:bg-gray-100 rounded-full transition-all"
                >
                    <ArrowLeft className="w-5 h-5 text-zinc-900" />
                </button>
                <div>
                    <h2 className="text-xl font-black text-zinc-900 italic tracking-tight leading-none uppercase">{profile?.full_name}</h2>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">
                        {isRecruiter ? "Recruiter" : "Job Seeker"} Profile
                    </p>
                </div>
            </div>

            {/* Profile Content */}
            <div className="bg-white border border-gray-100 rounded-[40px] overflow-hidden shadow-sm relative">
                {/* Cover Image */}
                <div className="relative h-64 w-full bg-zinc-900 overflow-hidden">
                    {profile?.cover_url ? (
                        <img src={profile.cover_url} alt="Cover" className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-zinc-950 opacity-50 relative overflow-hidden">
                             <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,102,255,0.1),transparent)]" />
                             {/* Abstract geometric shapes */}
                             <div className="absolute top-10 right-10 w-32 h-32 border border-white/5 rounded-full" />
                             <div className="absolute bottom-[-20px] left-[100px] w-64 h-64 border border-white/5 rounded-full" />
                        </div>
                    )}
                </div>

                {/* Profile Header (Avatar + Actions) */}
                <div className="relative px-8 pb-8">
                    <div className="flex justify-between items-end -mt-20 mb-6">
                        {/* Avatar */}
                        <div className="relative">
                            <div className="w-40 h-40 rounded-[48px] border-[6px] border-white bg-white overflow-hidden shadow-xl ring-1 ring-gray-100">
                                {profile?.avatar_url ? (
                                    <img src={profile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full bg-primary flex items-center justify-center text-4xl font-black text-white italic">
                                        {profile?.full_name?.[0]}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex space-x-3 pb-2">
                            <button className="p-3 border border-gray-100 rounded-[20px] hover:bg-gray-50 transition-all text-gray-500">
                                <MoreHorizontal className="w-5 h-5" />
                            </button>
                            <Link 
                                href="/dashboard/profile/edit"
                                className="px-8 py-3.5 bg-zinc-900 text-white rounded-[24px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-[1.03] transition-all flex items-center space-x-3"
                            >
                                <Edit3 className="w-4 h-4" />
                                <span>Modify Identity</span>
                            </Link>
                        </div>
                    </div>

                    {/* Personal Info */}
                    <div className="space-y-6">
                        <div>
                            <h1 className="text-4xl font-black text-zinc-900 italic tracking-tight mb-1">{profile?.full_name}</h1>
                            <p className="text-gray-500 font-bold uppercase tracking-widest flex items-center space-x-2">
                                <span className="text-primary italic font-black">@ operative</span>
                                <span className="w-1 h-1 bg-gray-300 rounded-full" />
                                <span>{isRecruiter ? "Recruiter" : "Engineering / Strategy"}</span>
                            </p>
                        </div>

                        {/* Bio */}
                        {profile?.bio ? (
                            <p className="text-lg text-zinc-600 font-medium leading-relaxed max-w-2xl">
                                {profile.bio}
                            </p>
                        ) : (
                            <p className="text-lg text-gray-400 font-bold italic">
                                No professional transmission received. Identity unconfirmed.
                            </p>
                        )}

                        {/* Meta Info */}
                        <div className="flex flex-wrap gap-y-4 gap-x-8">
                            <div className="flex items-center space-x-2 text-sm text-gray-500 font-bold">
                                <MapPin className="w-4 h-4 text-gray-400" />
                                <span>San Francisco, CA</span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-gray-500 font-bold">
                                <LinkIcon className="w-4 h-4 text-gray-400" />
                                <a href="#" className="text-primary hover:underline">hiresight.ai/james</a>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-gray-500 font-bold">
                                <Calendar className="w-4 h-4 text-gray-400" />
                                <span>Recruited April 2026</span>
                            </div>
                        </div>

                        {/* Professional Stats */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
                            <div className="p-4 bg-gray-50 rounded-[28px] border border-gray-100 text-center">
                                <div className="text-2xl font-black text-zinc-900 italic">28</div>
                                <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">Total Signals</div>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-[28px] border border-gray-100 text-center">
                                <div className="text-2xl font-black text-primary italic">94</div>
                                <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">AI Match Score</div>
                            </div>
                            <div className="p-4 bg-gray-50 rounded-[28px] border border-gray-100 text-center">
                                <div className="text-2xl font-black text-zinc-900 italic">15</div>
                                <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">Interviews</div>
                            </div>
                            <div className="p-4 bg-emerald-50 rounded-[28px] border border-emerald-100 text-center">
                                <div className="text-2xl font-black text-emerald-600 italic">85%</div>
                                <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">Hire Rate</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs / Sub-content */}
                <div className="border-t border-gray-50">
                    <div className="flex border-b border-gray-50 px-8">
                        {['Signals', 'Resume', 'Media', 'Affiliations'].map((tab, i) => (
                            <button 
                                key={tab} 
                                className={`px-6 py-5 text-sm font-black uppercase tracking-widest transition-all relative ${
                                    i === 0 ? 'text-zinc-900' : 'text-gray-400 hover:text-zinc-900'
                                }`}
                            >
                                {tab}
                                {i === 0 && <div className="absolute bottom-0 left-0 w-full h-1 bg-primary rounded-t-full" />}
                            </button>
                        ))}
                    </div>

                    <div className="p-10 space-y-10">
                        {/* Highlights Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="p-8 bg-zinc-900 rounded-[40px] text-white relative overflow-hidden group">
                                <div className="relative z-10 space-y-4">
                                    <div className="w-12 h-12 bg-white/10 rounded-2xl flex items-center justify-center text-primary">
                                        <Briefcase className="w-6 h-6" />
                                    </div>
                                    <h3 className="text-2xl font-black font-display italic tracking-tight">Professional Sync</h3>
                                    <p className="text-sm text-gray-400 font-bold leading-relaxed">
                                        Identity has been successfully linked with LinkedIn and GitHub protocols. 
                                        Reputation level: <span className="text-primary italic">PLATINUM</span>.
                                    </p>
                                </div>
                                <div className="absolute bottom-[-40px] right-[-40px] w-48 h-48 bg-primary/10 blur-[60px] rounded-full group-hover:scale-150 transition-transform duration-1000" />
                            </div>

                            <div className="p-8 bg-white border border-gray-100 rounded-[40px] space-y-4 group">
                                <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center text-secondary group-hover:bg-secondary/10 transition-colors">
                                    <Zap className="w-6 h-6" />
                                </div>
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tight">AI Engine Metrics</h3>
                                <p className="text-sm text-gray-500 font-bold leading-relaxed">
                                    Top Skills: <span className="text-secondary italic">Next.js</span>, <span className="text-secondary italic">Supabase</span>, <span className="text-secondary italic">Generative Intelligence</span>.
                                </p>
                            </div>
                        </div>

                        {/* Recent Activity / Experience Shell */}
                        <div className="space-y-6">
                            <h4 className="text-xl font-black text-zinc-900 italic uppercase tracking-tighter">Recent Operative Logs</h4>
                            {[1, 2].map(i => (
                                <div key={i} className="flex space-x-6 p-6 border border-gray-50 rounded-[32px] hover:bg-gray-50 transition-all">
                                    <div className="w-14 h-14 bg-white shadow-sm border border-gray-100 rounded-2xl flex items-center justify-center">
                                        <FileText className="w-6 h-6 text-primary" />
                                    </div>
                                    <div className="space-y-1">
                                        <h5 className="font-black text-zinc-900 italic">Senior Intelligence Engineer</h5>
                                        <p className="text-sm font-bold text-gray-500 uppercase tracking-widest">Protocol-X HQ · 2024 - Present</p>
                                        <p className="text-sm text-gray-400 font-medium pt-2">
                                            Architected high-scale generative agents and decentralized reputation systems.
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
