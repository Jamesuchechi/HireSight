"use client";

import { useEffect, useState, use } from "react";
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
    ArrowLeft,
    Shield,
    Globe,
    Phone,
    MessageSquare
} from "lucide-react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ProfileStats from "@/components/profile/ProfileStats";
import ExperienceTimeline from "@/components/profile/ExperienceTimeline";
import SkillBadgeGrid from "@/components/profile/SkillBadgeGrid";
import { ExtendedProfile } from "@/types/profile";

export default function PublicProfilePage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<ExtendedProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [isOwnProfile, setIsOwnProfile] = useState(false);

    useEffect(() => {
        const fetchProfile = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            
            if (user?.id === id) {
                setIsOwnProfile(true);
            }

            const { data: profileData, error } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", id)
                .single();

            if (profileData) {
                setProfile({
                    ...profileData,
                    skills: profileData.skills || [],
                    experience: profileData.experience || [],
                    education: profileData.education || [],
                    certifications: profileData.certifications || [],
                    portfolio_links: profileData.portfolio_links || [],
                    job_preferences: profileData.job_preferences || {},
                    company_data: profileData.company_data || {}
                } as ExtendedProfile);
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase, id]);

    if (loading) return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Accessing Public Protocol...</p>
        </div>
    );

    if (!profile) return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4 text-center">
            <h2 className="text-2xl font-black italic text-zinc-900 uppercase">Identity Not Found</h2>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">Protocol transmission failed. User does not exist.</p>
            <button onClick={() => router.back()} className="px-8 py-3 bg-zinc-900 text-white rounded-2xl font-black italic uppercase">Return to Base</button>
        </div>
    );

    const isRecruiter = profile?.role === "recruiter";

    const stats = isRecruiter ? [
        { label: "Jobs Active", value: "12", icon: Briefcase, color: "text-zinc-900", bgColor: "bg-gray-50", borderColor: "border-gray-100" },
        { label: "Hire Rate", value: "85%", icon: Zap, color: "text-primary", bgColor: "bg-primary/5", borderColor: "border-primary/10" },
        { label: "Avg. Fill Time", value: "18d", icon: Calendar, color: "text-zinc-900", bgColor: "bg-gray-50", borderColor: "border-gray-100" },
        { label: "Candidate Net", value: "4.2k", icon: Star, color: "text-zinc-900", bgColor: "bg-gray-50", borderColor: "border-gray-100" }
    ] : [
        { label: "Signal Strength", value: "94%", icon: Zap, color: "text-primary", bgColor: "bg-primary/5", borderColor: "border-primary/10" },
        { label: "InterViews Sync", value: "15", icon: Briefcase, color: "text-zinc-900", bgColor: "bg-gray-50", borderColor: "border-gray-100" },
        { label: "Reputation", value: "Gold", icon: Shield, color: "text-zinc-900", bgColor: "bg-gray-50", borderColor: "border-gray-100" },
        { label: "Hired Factor", value: "High", icon: Star, color: "text-emerald-600", bgColor: "bg-emerald-50", borderColor: "border-emerald-100" }
    ];

    return (
        <div className="max-w-5xl mx-auto pb-20 px-4 md:px-0">
            {/* Header / Nav */}
            <div className="flex items-center space-x-8 py-4 mb-2 sticky top-0 bg-white/80 backdrop-blur-md z-20">
                <button 
                    onClick={() => router.back()}
                    className="p-2 hover:bg-gray-100 rounded-full transition-all"
                >
                    <ArrowLeft className="w-5 h-5 text-zinc-900" />
                </button>
                <div>
                    <h2 className="text-xl font-black text-zinc-900 italic tracking-tight leading-none uppercase">{profile?.full_name}</h2>
                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">
                        {isRecruiter ? "Network Architect" : "Operative"} ID Protocol
                    </p>
                </div>
            </div>

            <div className="bg-white border border-gray-100 rounded-[40px] overflow-hidden shadow-2xl relative">
                {/* Cover Image */}
                <div className="relative h-64 w-full bg-zinc-900 overflow-hidden">
                    {profile?.cover_url ? (
                        <img src={profile.cover_url} alt="Cover" className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-zinc-950 opacity-50 relative overflow-hidden">
                             <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,102,255,0.1),transparent)]" />
                        </div>
                    )}
                </div>

                <div className="relative px-6 md:px-12 pb-12">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end -mt-20 mb-8 space-y-6 md:space-y-0">
                        <div className="relative">
                            <div className="w-40 h-40 rounded-[48px] border-[6px] border-white bg-white overflow-hidden shadow-2xl ring-1 ring-gray-100">
                                {profile?.avatar_url ? (
                                    <img src={profile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full bg-primary flex items-center justify-center text-4xl font-black text-white italic">
                                        {profile?.full_name?.[0]}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex space-x-3 pb-2 w-full md:w-auto">
                            {!isOwnProfile ? (
                                <>
                                    <button className="p-4 border border-gray-100 rounded-[24px] hover:bg-gray-50 transition-all text-gray-500 shadow-sm">
                                        <MoreHorizontal className="w-5 h-5" />
                                    </button>
                                    <Link 
                                        href={`/dashboard/messages?recipient=${profile.id}`}
                                        className="flex-1 md:flex-none px-8 py-4 bg-primary text-white rounded-[28px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center justify-center space-x-3 border-b-4 border-zinc-900"
                                    >
                                        <MessageSquare className="w-4 h-4" />
                                        <span>Initiate Sync</span>
                                    </Link>
                                </>
                            ) : (
                                <Link 
                                    href="/dashboard/profile/edit"
                                    className="flex-1 md:flex-none px-8 py-4 bg-zinc-900 text-white rounded-[28px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center justify-center space-x-3 border-b-4 border-primary"
                                >
                                    <Edit3 className="w-4 h-4" />
                                    <span>Refine Protocol</span>
                                </Link>
                            )}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                        <div className="lg:col-span-12 space-y-8">
                            <div className="space-y-4">
                                <div>
                                    <h1 className="text-5xl font-black text-zinc-900 italic tracking-tight mb-2 drop-shadow-sm">{profile?.full_name}</h1>
                                    <p className="text-gray-500 font-bold uppercase tracking-widest flex flex-wrap items-center gap-2">
                                        <span className="text-primary italic font-black text-lg">
                                            {profile?.headline || (isRecruiter ? "Managing Director" : "Protocol Engineer")}
                                        </span>
                                    </p>
                                </div>
                                <div className="bg-gray-50/50 p-8 rounded-[32px] border border-gray-100">
                                    <p className="text-lg text-zinc-600 font-medium leading-relaxed max-w-3xl italic">
                                        "{profile?.bio || "No professional transmission received."}"
                                    </p>
                                </div>
                            </div>
                            <ProfileStats stats={stats} />
                        </div>

                        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-12">
                            <div className="md:col-span-2 space-y-12">
                                <ExperienceTimeline experiences={profile?.experience || []} />
                            </div>
                            <div className="space-y-12">
                                <div className="bg-zinc-900 p-8 rounded-[40px] text-white relative overflow-hidden group">
                                    <div className="relative z-10 space-y-6">
                                        <h4 className="text-xl font-black font-display italic tracking-tight uppercase border-b border-white/10 pb-4">Skill Matrix</h4>
                                        <SkillBadgeGrid skills={profile?.skills || []} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
