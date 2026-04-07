"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
    Briefcase, FileText, Send, Zap, Clock, Star, 
    TrendingUp, Search, ArrowUpRight, MapPin, 
    BrainCircuit, Users, Rocket, ChevronRight,
    SearchCheck, ShieldCheck, Mail, Calendar
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import ResumeUpload from "@/components/ResumeUpload";
import { 
    StatCard, 
    ProfileProgress, 
    HiringFunnel, 
    RecommendedJobs, 
    InterviewCalendar 
} from "@/components/dashboard/DashboardWidgets";
import { 
    getCandidateDashboardData, 
    getRecruiterDashboardData 
} from "@/lib/supabase/dashboard";

export default function Dashboard() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<any>(null);
    const [dashboardData, setDashboardData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboard = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data: profileData } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            if (profileData) {
                setProfile(profileData);
                const data = profileData.role === "recruiter" 
                    ? await getRecruiterDashboardData(supabase as any, user.id)
                    : await getCandidateDashboardData(supabase as any, user.id);
                setDashboardData(data);
            }
            setLoading(false);
        };
        fetchDashboard();
    }, [supabase, router]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    const isRecruiter = profile?.role === "recruiter";

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-32">
            {/* Header / Welcome */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between space-y-8">
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <div className="flex items-center space-x-3 mb-2">
                        <span className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest rounded-full italic">Protocol Active</span>
                        <span className="text-[10px] font-black text-gray-300 uppercase tracking-widest">• HireSight v2.0</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Synchronize, <span className="text-primary tracking-normal">{isRecruiter ? (profile?.company_name || 'Matrix Corp') : profile?.full_name?.split(' ')[0]}</span>
                    </h1>
                    <p className="text-gray-500 font-bold max-w-lg mt-4 italic">
                        {isRecruiter 
                            ? "Your mission control for talent acquisition and elite vetting cycles." 
                            : "Accelerate your career trajectory with AI-driven matching and direct company links."}
                    </p>
                </motion.div>
                
                <div className="flex items-center space-x-4">
                    <button className="px-8 py-5 bg-white border border-gray-100 rounded-[32px] font-black text-xs uppercase tracking-widest text-zinc-500 hover:bg-gray-50 transition-all flex items-center space-x-2">
                        <Mail className="w-4 h-4" />
                        <span>Intelligence Feed</span>
                    </button>
                    <button 
                        onClick={() => router.push(isRecruiter ? "/dashboard/jobs/create" : "/jobs")}
                        className="px-10 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-sm uppercase tracking-widest italic shadow-xl hover:scale-[1.05] transition-all flex items-center space-x-2"
                    >
                        <PlusIcon className="w-4 h-4" />
                        <span>{isRecruiter ? "Initialize Job" : "Explore Vector"}</span>
                    </button>
                </div>
            </header>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                {isRecruiter ? (
                    <>
                        <StatCard icon={<Briefcase />} title="Active Nodes" value={dashboardData.stats.activeJobs} color="bg-primary text-primary" delay={0.1} />
                        <StatCard icon={<Users />} title="Pending Review" value={dashboardData.stats.totalApplicants} color="bg-secondary text-secondary" delay={0.2} />
                        <StatCard icon={<Calendar />} title="Syncs This Week" value={dashboardData.stats.interviewsThisWeek} color="bg-purple-500 text-purple-500" delay={0.3} />
                        <StatCard icon={<ShieldCheck />} title="Hired Month" value={dashboardData.stats.hiredThisMonth} color="bg-emerald-500 text-emerald-500" delay={0.4} />
                    </>
                ) : (
                    <>
                        <StatCard icon={<Rocket />} title="Active Vectors" value={dashboardData.stats.activeApplications} color="bg-primary text-primary" delay={0.1} />
                        <StatCard icon={<Star />} title="Saved Sectors" value={dashboardData.stats.savedJobs} color="bg-amber-500 text-amber-500" delay={0.2} />
                        <StatCard icon={<SearchCheck />} title="Neural Matches" value={dashboardData.stats.recommendedCount} color="bg-secondary text-secondary" delay={0.3} />
                        <StatCard icon={<Users />} title="Matrix Views" value={dashboardData.stats.profileViews} color="bg-emerald-500 text-emerald-500" delay={0.4} />
                    </>
                )}
            </div>

            {/* Main Interactive Matrix */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                <div className="lg:col-span-2 space-y-12">
                    {/* Role-Specific Secondary Features */}
                    {isRecruiter ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <HiringFunnel data={dashboardData.funnel} />
                            <div className="bg-white border border-gray-100 rounded-[56px] p-10 shadow-sm space-y-8">
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tighter">Elite Candidates</h3>
                                <div className="space-y-4">
                                    {dashboardData.topCandidates.map((c: any) => (
                                        <div key={c.id} className="p-4 border border-gray-50 rounded-[28px] hover:bg-gray-50/50 transition-all flex items-center justify-between group">
                                            <div className="flex items-center space-x-4">
                                                <div className="w-12 h-12 bg-gray-100 rounded-2xl flex items-center justify-center font-black text-xs italic uppercase">
                                                    {c.candidate?.avatar_url ? <img src={c.candidate.avatar_url} className="w-full h-full object-cover rounded-2xl" /> : c.candidate?.full_name?.[0]}
                                                </div>
                                                <div>
                                                    <h5 className="font-black text-zinc-900 italic tracking-tight">{c.candidate?.full_name}</h5>
                                                    <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">{c.job?.title}</p>
                                                </div>
                                            </div>
                                            <div className="text-xl font-black text-primary italic leading-none">{c.match_score}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <RecommendedJobs jobs={dashboardData.recommendedJobs} />
                            <div className="bg-white border border-gray-100 rounded-[56px] p-10 shadow-sm space-y-8 flex flex-col justify-center text-center items-center">
                                <div className="p-6 bg-primary/10 text-primary rounded-[32px] mb-4">
                                    <BrainCircuit className="w-10 h-10" />
                                </div>
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tighter uppercase">AI Resume Refinement</h3>
                                <p className="text-xs text-gray-400 font-bold max-w-xs leading-relaxed italic">Upload your latest PDF protocol to re-align your neural match vectors.</p>
                                <div className="w-full mt-6">
                                    <ResumeUpload onSuccess={() => router.refresh()} />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Uniform Activity Segment */}
                    <div className="bg-white border border-gray-100 rounded-[56px] shadow-sm p-10">
                        <div className="flex items-center justify-between mb-10">
                            <div>
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic tracking-tighter">Timeline Logs</h3>
                                <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 italic italic">Recent chronological updates from the Hiring matrix</p>
                            </div>
                            <button className="px-6 py-3 bg-gray-50 border border-gray-100 rounded-2xl text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:bg-zinc-900 hover:text-white transition-all shadow-sm">Audit Archives</button>
                        </div>
                        
                        <div className="space-y-6">
                            {(isRecruiter ? dashboardData.recentActivity : dashboardData.recentApplications).map((item: any) => (
                                <div key={item.id} className="group p-5 border border-gray-50 rounded-2xl flex items-center justify-between hover:bg-gray-50/50 transition-all cursor-pointer">
                                    <div className="flex items-center space-x-6">
                                        <div className="w-14 h-14 bg-white border border-gray-100 rounded-2xl shadow-sm flex items-center justify-center font-black text-zinc-300 transition-all group-hover:text-primary">
                                            {isRecruiter ? <Users className="w-6 h-6" /> : <Briefcase className="w-6 h-6" />}
                                        </div>
                                        <div>
                                            <h5 className="font-black text-zinc-900 italic tracking-tight uppercase">
                                                {isRecruiter ? item.candidate?.full_name : item.job?.title}
                                            </h5>
                                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1 italic">
                                                {isRecruiter ? `Applied for ${item.job?.title}` : "Stripe • Final Review Stage"}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-3">
                                        <span className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest italic ${
                                            item.status === 'hired' ? 'bg-emerald-50 text-emerald-500' : 
                                            item.status === 'rejected' ? 'bg-rose-50 text-rose-500' : 'bg-primary/5 text-primary'
                                        }`}>
                                            {item.status}
                                        </span>
                                        <ChevronRight className="w-4 h-4 text-gray-300 group-hover:translate-x-1 transition-transform" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Performance & Sync Vector (Sidebar) */}
                <div className="space-y-12">
                    <ProfileProgress score={dashboardData.profileCompletion} />
                    <InterviewCalendar interviews={dashboardData.interviews} />
                    
                    {/* Neural Analytics Upsell */}
                    <div className="bg-gradient-to-br from-zinc-900 to-[#121214] rounded-[48px] p-10 shadow-2xl space-y-8 relative overflow-hidden group">
                         <div className="relative z-10 space-y-6">
                            <div className="inline-flex items-center space-x-2 px-3 py-1 bg-white/10 rounded-full border border-white/5">
                                <Zap className="w-3 h-3 text-primary animate-pulse" />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">Upgrade to Neural Pro</span>
                            </div>
                            <h3 className="text-2xl font-black font-display text-white italic tracking-tight">
                                Unlock recursive intelligence tracking.
                            </h3>
                            <button className="w-full py-5 bg-white text-zinc-900 rounded-[32px] font-black text-[10px] uppercase tracking-widest italic hover:scale-[1.03] transition-all flex items-center justify-center space-x-2 shadow-2xl">
                                <span>Activate Protocol</span>
                                <ArrowUpRight className="w-4 h-4" />
                            </button>
                         </div>
                         <div className="absolute right-0 top-0 w-48 h-48 bg-primary/20 blur-[100px] rounded-full pointer-events-none opacity-50 group-hover:scale-125 transition-transform duration-1000" />
                    </div>
                </div>
            </div>
        </div>
    );
}

function PlusIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 12h14" />
      <path d="M12 5v14" />
    </svg>
  );
}
