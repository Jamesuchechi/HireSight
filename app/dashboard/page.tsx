"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Briefcase, FileText, Send, Zap, Clock, Star, TrendingUp, Search, ArrowUpRight, MapPin } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

const SidebarItem = ({ icon, title, value, color }: { icon: React.ReactNode, title: string, value: string | number, color: string }) => (
    <div className="p-6 bg-white border border-gray-100 rounded-[32px] shadow-sm hover:shadow-xl transition-all group overflow-hidden relative">
        <div className={`p-3 rounded-2xl ${color} bg-opacity-10 text-opacity-100 inline-flex items-center justify-center mb-4 transition-transform group-hover:scale-110`}>
            {icon}
        </div>
        <p className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">{title}</p>
        <h4 className="text-3xl font-black text-zinc-900 italic tracking-tight">{value}</h4>
        
        {/* Background decorative element */}
        <div className={`absolute -right-4 -bottom-4 w-20 h-20 ${color} opacity-[0.03] rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700`} />
    </div>
);

export default function Dashboard() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const checkUser = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return; // Layout handles redirect

            const { data: profile } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            if (profile) {
                if (!profile.onboarding_completed && window.location.pathname !== '/onboarding') {
                    // router.push("/onboarding"); // Uncomment when onboarding is ready
                }
                setProfile(profile);
            }
            setLoading(false);
        };
        checkUser();
    }, [supabase, router]);

    if (loading) return null;

    const isRecruiter = profile?.role === "recruiter";

    return (
        <div className="max-w-7xl mx-auto space-y-10">
            {/* Header / Welcome */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between space-y-4">
                <div>
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 mb-2 italic tracking-tighter">
                        Welcome back, <span className="text-primary tracking-normal">{profile?.full_name?.split(' ')[0]}!</span>
                    </h1>
                    <p className="text-gray-500 font-bold">You have <span className="text-primary italic font-black">3 new</span> notifications and your profile is <span className="text-primary font-black italic">85% optimized</span>.</p>
                </div>
                <div className="flex items-center space-x-3">
                    <button className="px-6 py-3 bg-white border border-gray-100 rounded-2xl font-black text-xs uppercase tracking-widest text-zinc-500 hover:bg-gray-50 transition-all">
                        Edit Schedule
                    </button>
                    <button className="px-6 py-3 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest italic shadow-xl hover:scale-[1.03] transition-all">
                        {isRecruiter ? "Post New Job" : "New Application"}
                    </button>
                </div>
            </header>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {isRecruiter ? (
                    <>
                        <SidebarItem icon={<Briefcase />} title="Active Jobs" value="12" color="bg-primary text-primary" />
                        <SidebarItem icon={<Send />} title="Total Applicants" value="482" color="bg-secondary text-secondary" />
                        <SidebarItem icon={<Zap />} title="AI Screened" value="15.2k" color="bg-accent text-accent" />
                        <SidebarItem icon={<TrendingUp />} title="Hiring Rate" value="+24%" color="bg-emerald-500 text-emerald-500" />
                    </>
                ) : (
                    <>
                        <SidebarItem icon={<Clock />} title="Active Apps" value="08" color="bg-primary text-primary" />
                        <SidebarItem icon={<Send />} title="Matches Found" value="156" color="bg-secondary text-secondary" />
                        <SidebarItem icon={<Zap />} title="AI Score" value="94" color="bg-accent text-accent" />
                        <SidebarItem icon={<Star />} title="Saved Jobs" value="23" color="bg-emerald-500 text-emerald-500" />
                    </>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content Area */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Activity Feed / List */}
                    <div className="bg-white border border-gray-100 rounded-[40px] shadow-sm p-8">
                        <div className="flex items-center justify-between mb-8">
                            <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tight">
                                {isRecruiter ? "Recent Applicants" : "Active Applications"}
                            </h3>
                            <button className="text-xs font-black uppercase text-primary hover:underline">View All</button>
                        </div>
                        
                        <div className="space-y-4">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="group p-4 border border-gray-50 rounded-2xl flex items-center justify-between hover:bg-gray-50/50 transition-all cursor-pointer">
                                    <div className="flex items-center space-x-4">
                                        <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center font-black text-gray-400 group-hover:bg-white group-hover:shadow-sm transition-all">
                                            {isRecruiter ? "SC" : <Briefcase className="w-5 h-5" />}
                                        </div>
                                        <div>
                                            <h5 className="font-black text-zinc-900 italic">
                                                {isRecruiter ? "Sarah Chen" : "Software Engineer III"}
                                            </h5>
                                            <p className="text-xs text-gray-500 font-bold">
                                                {isRecruiter ? "Applying for Senior Backend" : "Stripe - San Francisco"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-lg font-black text-primary italic">98%</div>
                                        <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Match</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* AI Recommendation Banner */}
                    <div className="bg-gradient-to-br from-zinc-900 to-[#121214] rounded-[40px] p-10 flex items-center justify-between overflow-hidden relative group">
                         <div className="relative z-10 space-y-6">
                            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full">
                                <Zap className="w-3 h-3 text-primary animate-pulse" />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">HireSight AI Engine</span>
                            </div>
                            <h3 className="text-3xl font-black font-display text-white italic tracking-tight">
                                {isRecruiter ? "Optimize your job requirements with AI." : "Get matched with higher paying roles instantly."}
                            </h3>
                            <button className="px-8 py-4 bg-white text-zinc-900 rounded-2xl font-black text-sm hover:scale-[1.05] transition-all flex items-center space-x-2">
                                <span>Learn More</span>
                                <ArrowUpRight className="w-4 h-4 ml-1" />
                            </button>
                         </div>
                         <div className="hidden md:block relative z-10">
                            <div className="w-32 h-32 bg-primary/20 blur-3xl rounded-full" />
                         </div>
                         {/* Abstract grid in background */}
                         <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)', backgroundSize: '24px 24px' }} />
                    </div>
                </div>

                {/* Sidebar Column */}
                <div className="space-y-8">
                     {/* User Progress */}
                     <div className="bg-white border border-gray-100 shadow-sm rounded-[40px] p-8">
                        <h4 className="text-xl font-black font-display text-zinc-900 mb-6 italic">Performance</h4>
                        <div className="space-y-6 text-center">
                            <div className="relative w-40 h-40 mx-auto">
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" className="text-gray-100" />
                                    <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="12" fill="transparent" strokeDasharray="440" strokeDashoffset="66" className="text-primary transition-all duration-1000" />
                                </svg>
                                <div className="absolute inset-0 flex flex-col items-center justify-center">
                                    <span className="text-4xl font-black italic text-zinc-900">85%</span>
                                    <span className="text-[8px] font-black text-gray-400 uppercase tracking-widest mt-1">Overall Optimized</span>
                                </div>
                            </div>
                            <p className="text-sm font-bold text-gray-500 leading-relaxed px-4">
                                Keep updating your {isRecruiter ? "job descriptions" : "resume"} to maintain a top-tier match score.
                            </p>
                        </div>
                     </div>

                     {/* Upcoming Interviews */}
                     <div className="bg-white border border-gray-100 shadow-sm rounded-[40px] p-8">
                         <div className="flex items-center justify-between mb-8">
                            <h4 className="text-xl font-black font-display text-zinc-900 italic tracking-tight underline decoration-primary/20 decoration-4">Agenda</h4>
                            <div className="p-2 bg-primary/5 rounded-xl text-primary">
                                <FileText className="w-4 h-4" />
                            </div>
                         </div>
                         <div className="space-y-6">
                            {[1, 2].map(i => (
                                <div key={i} className="flex space-x-4 border-l-4 border-primary pl-4 py-1">
                                    <div className="text-sm">
                                        <p className="font-black text-zinc-900 italic leading-none mb-1">Interview with {isRecruiter ? "Google" : "Stripe"}</p>
                                        <p className="text-xs text-gray-400 font-bold uppercase tracking-widest mb-1">Tomorrow, 10:00 AM</p>
                                        <div className="flex items-center space-x-1 text-[10px] font-black text-primary uppercase tracking-tighter">
                                            <MapPin className="w-2.5 h-2.5" />
                                            <span>Virtual Room</span>
                                        </div>
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
