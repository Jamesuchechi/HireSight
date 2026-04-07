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
    ArrowLeft,
    Shield,
    Globe,
    Phone
} from "lucide-react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import ProfileStats from "@/components/profile/ProfileStats";
import ExperienceTimeline from "@/components/profile/ExperienceTimeline";
import SkillBadgeGrid from "@/components/profile/SkillBadgeGrid";
import { ExtendedProfile } from "@/types/profile";

export default function ProfilePage() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<ExtendedProfile | null>(null);
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
                // Ensure array fields are actually arrays (Supabase might return null if not initialized)
                setProfile({
                    ...profile,
                    skills: profile.skills || [],
                    experience: profile.experience || [],
                    education: profile.education || [],
                    certifications: profile.certifications || [],
                    portfolio_links: profile.portfolio_links || [],
                    job_preferences: profile.job_preferences || {},
                    company_data: profile.company_data || {}
                } as ExtendedProfile);
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase, router]);

    if (loading) return null;

    const isRecruiter = profile?.role === "recruiter";

    // Calculate dynamic stats
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

            {/* Profile Content */}
            <div className="bg-white border border-gray-100 rounded-[40px] overflow-hidden shadow-2xl relative">
                {/* Cover Image */}
                <div className="relative h-64 w-full bg-zinc-900 overflow-hidden">
                    {profile?.cover_url ? (
                        <img src={profile.cover_url} alt="Cover" className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full bg-gradient-to-br from-zinc-800 to-zinc-950 opacity-50 relative overflow-hidden">
                             <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,102,255,0.1),transparent)]" />
                             <div className="absolute top-10 right-10 w-32 h-32 border border-white/5 rounded-full" />
                             <div className="absolute bottom-[-20px] left-[100px] w-64 h-64 border border-white/5 rounded-full" />
                        </div>
                    )}
                </div>

                {/* Profile Header (Avatar + Actions) */}
                <div className="relative px-6 md:px-12 pb-12">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end -mt-20 mb-8 space-y-6 md:space-y-0">
                        {/* Avatar */}
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

                        {/* Actions */}
                        <div className="flex space-x-3 pb-2 w-full md:w-auto">
                            <button className="p-4 border border-gray-100 rounded-[24px] hover:bg-gray-50 transition-all text-gray-500 shadow-sm">
                                <MoreHorizontal className="w-5 h-5" />
                            </button>
                            <Link 
                                href="/dashboard/profile/edit"
                                className="flex-1 md:flex-none px-8 py-4 bg-zinc-900 text-white rounded-[28px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center justify-center space-x-3 border-b-4 border-primary"
                            >
                                <Edit3 className="w-4 h-4" />
                                <span>Refine Protocol</span>
                            </Link>
                        </div>
                    </div>

                    {/* Identity Details */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                        {/* Left Column: Core Identity */}
                        <div className="lg:col-span-12 space-y-8">
                            <div className="space-y-4">
                                <div>
                                    <h1 className="text-5xl font-black text-zinc-900 italic tracking-tight mb-2 drop-shadow-sm">{profile?.full_name}</h1>
                                    <p className="text-gray-500 font-bold uppercase tracking-widest flex flex-wrap items-center gap-2">
                                        <span className="text-primary italic font-black text-lg">
                                            {profile?.headline || (isRecruiter ? "Managing Director" : "Protocol Engineer")}
                                        </span>
                                        <span className="w-1.5 h-1.5 bg-gray-300 rounded-full hidden md:block" />
                                        <span className="text-gray-400">
                                            {isRecruiter ? (profile?.company_data?.industry || "Intelligence Agency") : "@ freelance operative"}
                                        </span>
                                    </p>
                                </div>

                                {/* Meta Meta info */}
                                <div className="flex flex-wrap gap-y-4 gap-x-8 border-t border-b border-gray-50 py-6">
                                    <div className="flex items-center space-x-2 text-sm text-zinc-900 font-black italic">
                                        <MapPin className="w-4 h-4 text-primary" />
                                        <span className="uppercase tracking-wider">{profile?.location || "San Francisco, CA"}</span>
                                    </div>
                                    <div className="flex items-center space-x-2 text-sm text-zinc-900 font-black italic">
                                        <Globe className="w-4 h-4 text-primary" />
                                        <a href="#" className="uppercase tracking-wider hover:text-primary transition-colors">Digital HQ</a>
                                    </div>
                                    <div className="flex items-center space-x-2 text-sm text-zinc-900 font-black italic">
                                        <Phone className="w-4 h-4 text-primary" />
                                        <span className="uppercase tracking-wider">{profile?.phone || "REDACTED"}</span>
                                    </div>
                                    <div className="flex items-center space-x-2 text-sm text-gray-400 font-black italic">
                                        <Calendar className="w-4 h-4" />
                                        <span className="uppercase tracking-wider">COMMS EST. {new Date(profile?.updated_at || "").getFullYear()}</span>
                                    </div>
                                </div>

                                {/* Bio */}
                                <div className="bg-gray-50/50 p-8 rounded-[32px] border border-gray-100">
                                    <p className="text-lg text-zinc-600 font-medium leading-relaxed max-w-3xl italic">
                                        "{profile?.bio || "No professional transmission received. Identity currently in ghost protocol. System awaits update."}"
                                    </p>
                                </div>
                            </div>

                            {/* Stats */}
                            <ProfileStats stats={stats} />
                        </div>

                        {/* Middle & Right Content */}
                        <div className="lg:col-span-12 grid grid-cols-1 md:grid-cols-3 gap-12">
                            {/* Main Feed: Experience */}
                            <div className="md:col-span-2 space-y-12">
                                <ExperienceTimeline experiences={profile?.experience || []} />
                                
                                <div className="space-y-6">
                                    <h4 className="text-xl font-black text-zinc-900 italic uppercase tracking-tighter flex items-center space-x-3">
                                        <span className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center">
                                            <FileText className="w-4 h-4 text-primary" />
                                        </span>
                                        <span>Academic Credentials</span>
                                    </h4>
                                    <div className="grid grid-cols-1 gap-4">
                                        {(profile?.education || []).map((edu, i) => (
                                            <div key={i} className="p-6 bg-white border border-gray-100 rounded-[32px] hover:shadow-lg transition-all group">
                                                <h5 className="font-black text-zinc-900 italic text-lg">{edu.degree} in {edu.field}</h5>
                                                <p className="text-sm font-bold text-primary uppercase tracking-widest mt-1">{edu.institution}</p>
                                                <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-2">Class of {edu.end_year}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Sidebar: Skills & Utils */}
                            <div className="space-y-12">
                                <div className="bg-zinc-900 p-8 rounded-[40px] text-white relative overflow-hidden group">
                                    <div className="relative z-10 space-y-6">
                                        <h4 className="text-xl font-black font-display italic tracking-tight uppercase border-b border-white/10 pb-4">Skill Matrix</h4>
                                        <SkillBadgeGrid skills={profile?.skills || []} />
                                        <button className="w-full py-4 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl text-[10px] font-black uppercase tracking-widest italic transition-all">
                                            Export Competency Report
                                        </button>
                                    </div>
                                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 blur-[60px] rounded-full" />
                                </div>

                                <div className="space-y-6">
                                    <h4 className="text-xl font-black text-zinc-900 italic uppercase tracking-tighter flex items-center space-x-3">
                                        <Star className="w-5 h-5 text-primary" />
                                        <span>Identity Links</span>
                                    </h4>
                                    <div className="space-y-3">
                                        {(profile?.portfolio_links || []).map((link, i) => (
                                            <a 
                                                key={i} 
                                                href={link.url} 
                                                target="_blank" 
                                                className="flex items-center justify-between p-4 bg-gray-50 border border-gray-100 rounded-2xl hover:bg-white hover:border-primary/30 transition-all group"
                                            >
                                                <span className="font-black italic text-xs uppercase tracking-widest text-zinc-600 group-hover:text-primary">{link.type}</span>
                                                <LinkIcon className="w-4 h-4 text-gray-400 group-hover:text-primary" />
                                            </a>
                                        ))}
                                        {(profile?.portfolio_links?.length || 0) === 0 && (
                                            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest italic px-2">No external links established.</p>
                                        )}
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
