import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import { 
    MapPin, Briefcase, DollarSign, Clock, 
    ChevronLeft, Share2, Star, Zap, 
    CheckCircle2, BrainCircuit, Building2 
} from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import { Database } from "@/types/database";
import JobViewTracker from "@/components/jobs/JobViewTracker";

type Job = Database["public"]["Tables"]["jobs"]["Row"];
type Skill = Database["public"]["Tables"]["job_skills"]["Row"];

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const supabase = await createClient();
    const { id } = await params;

    const { data: job, error } = await supabase
        .from("jobs")
        .select(`
            *,
            profiles!company_id(full_name, avatar_url),
            job_skills (*),
            job_screening_questions (*)
        `)
        .eq("id", id)
        .single();

    if (error || !job) {
        notFound();
    }

    return (
        <div className="min-h-screen bg-gray-50/30 pt-32 pb-24">
            <JobViewTracker jobId={id} />
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                {/* Back & Share Actions */}
                <div className="flex items-center justify-between mb-12">
                    <Link 
                        href="/jobs"
                        className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                    >
                        <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                        <span>Return to Global Discovery</span>
                    </Link>
                    <div className="flex items-center space-x-4">
                        <button className="p-3 bg-white border border-gray-100 rounded-2xl text-gray-400 hover:text-primary transition-all">
                            <Share2 className="w-5 h-5" />
                        </button>
                        <button className="p-3 bg-white border border-gray-100 rounded-2xl text-gray-400 hover:text-primary transition-all">
                            <Star className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                    {/* Main Content (Left) */}
                    <div className="lg:col-span-2 space-y-12">
                        {/* Header Section */}
                        <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm relative overflow-hidden group">
                             {/* Decorative Background */}
                             <div className="absolute -right-20 -top-20 w-80 h-80 bg-primary/5 rounded-full blur-[100px] pointer-events-none" />
                             <div className="absolute -left-20 -bottom-20 w-60 h-60 bg-secondary/5 rounded-full blur-[100px] pointer-events-none" />

                             <div className="relative z-10 space-y-8">
                                <div className="flex items-start justify-between">
                                    <div className="space-y-4">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-16 h-16 bg-gray-50 rounded-[24px] border border-gray-100 flex items-center justify-center font-black text-primary italic shadow-sm overflow-hidden">
                                                {(job as any).profiles?.avatar_url ? (
                                                  <img src={(job as any).profiles.avatar_url} alt={(job as any).profiles.full_name || ""} className="w-full h-full object-cover" />
                                                ) : (
                                                  <span className="text-xl">{(job as any).profiles?.full_name?.substring(0, 1).toUpperCase() || job.title.substring(0, 1).toUpperCase()}</span>
                                                )}
                                            </div>
                                            <div>
                                                <h1 className="text-3xl md:text-4xl font-black font-display text-zinc-900 italic tracking-tighter leading-tight">
                                                    {job.title}
                                                </h1>
                                                <div className="flex items-center space-x-2 mt-1">
                                                    <span className="text-xs font-black uppercase text-primary tracking-widest">
                                                        {(job as any).profiles?.full_name || "Enterprise Partner"}
                                                    </span>
                                                    <div className="w-1 h-1 rounded-full bg-gray-200" />
                                                    <span className="text-[10px] font-bold text-gray-400 italic">Posted {formatDistanceToNow(new Date(job.created_at))} ago</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="hidden md:flex flex-col items-end">
                                        <div className="flex items-center space-x-2 bg-emerald-50 text-emerald-600 px-4 py-2 rounded-2xl border border-emerald-100">
                                            <Zap className="w-4 h-4 animate-pulse" />
                                            <span className="text-xs font-black uppercase tracking-widest">Priority Matching</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-8 border-t border-gray-50">
                                    <div className="space-y-1">
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Location</p>
                                        <div className="flex items-center space-x-2 text-zinc-900 font-bold italic">
                                            <MapPin className="w-4 h-4 text-primary" />
                                            <span className="text-sm">{job.location || "Remote"}</span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Salary Range</p>
                                        <div className="flex items-center space-x-2 text-zinc-900 font-bold italic">
                                            <DollarSign className="w-4 h-4 text-primary" />
                                            <span className="text-sm">${((job.salary_min || 0) / 1000).toFixed(0)}k - ${((job.salary_max || 0) / 1000).toFixed(0)}k</span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Job Type</p>
                                        <div className="flex items-center space-x-2 text-zinc-900 font-bold italic">
                                            <Briefcase className="w-4 h-4 text-primary" />
                                            <span className="text-sm capitalize">{job.job_type}</span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Experience</p>
                                         <div className="flex items-center space-x-2 text-zinc-900 font-bold italic">
                                            <BrainCircuit className="w-4 h-4 text-primary" />
                                            <span className="text-sm capitalize">{job.experience_level}</span>
                                        </div>
                                    </div>
                                </div>
                             </div>
                        </div>

                        {/* Description Section */}
                        <div className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm space-y-10">
                            <div className="space-y-6">
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase underline decoration-primary/20 decoration-4 underline-offset-8">Mission Protocol</h3>
                                <div 
                                    className="prose prose-zinc prose-sm max-w-none font-body text-gray-600 leading-relaxed job-content"
                                    dangerouslySetInnerHTML={{ __html: job.description }} 
                                />
                            </div>

                            {job.requirements && (
                                <div className="space-y-6 pt-10 border-t border-gray-50">
                                    <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Core Constraints</h3>
                                    <p className="text-sm text-gray-600 leading-relaxed font-body">
                                        {job.requirements}
                                    </p>
                                </div>
                            )}

                            {/* Skills Vector */}
                            <div className="space-y-6 pt-10 border-t border-gray-50">
                                <h3 className="text-2xl font-black font-display text-zinc-900 italic uppercase">Neural Matrix (Skills)</h3>
                                <div className="flex flex-wrap gap-3">
                                    {(job as any).job_skills?.map((skill: any) => (
                                        <div key={skill.id} className={`px-4 py-2 rounded-2xl border text-[10px] font-black uppercase tracking-widest flex items-center space-x-2 ${
                                            skill.is_required 
                                                ? "bg-primary text-white border-primary shadow-lg shadow-primary/20" 
                                                : "bg-white text-gray-500 border-gray-100"
                                        }`}>
                                            {skill.is_required && <CheckCircle2 className="w-3 h-3" />}
                                            <span>{skill.skill_name}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar (Right) */}
                    <div className="space-y-8">
                         {/* Application Card */}
                         <div className="bg-zinc-900 rounded-[48px] p-10 shadow-2xl space-y-8 sticky top-32">
                             <div className="space-y-2">
                                <h4 className="text-3xl font-black text-white italic tracking-tighter">Ready to Deploy?</h4>
                                <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic leading-relaxed">Join the HireSight network and initiate your career transition today.</p>
                             </div>

                             <div className="space-y-4">
                                <Link
                                    href={`/jobs/${id}/apply`}
                                    className="w-full py-5 bg-primary text-white rounded-[24px] font-black text-sm uppercase tracking-widest italic flex items-center justify-center space-x-3 hover:scale-[1.03] active:scale-[0.97] transition-all shadow-xl shadow-primary/30"
                                >
                                    <span>Initiate Application</span>
                                    <Zap className="w-4 h-4" />
                                </Link>
                                <p className="text-[10px] text-gray-500 text-center font-black uppercase tracking-widest italic">Average Processing latency: 2.4 days</p>
                             </div>

                             <div className="pt-8 border-t border-white/5 space-y-6">
                                <div className="flex items-center space-x-4">
                                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-primary">
                                        <Building2 className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Company Protocol</p>
                                        <p className="text-sm font-bold text-white italic">
                                            {(job as any).profiles?.full_name || "Verified Organization"}
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-4">
                                     <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-secondary">
                                        <Clock className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Expiring In</p>
                                        <p className="text-sm font-bold text-white italic">{job.expires_at ? formatDistanceToNow(new Date(job.expires_at)) : "Never"}</p>
                                    </div>
                                </div>
                             </div>
                         </div>

                         {/* Share/External Links */}
                         <div className="bg-white border border-gray-100 rounded-[40px] p-8 shadow-sm">
                             <h5 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-6">Discovery Source</h5>
                             <div className="flex items-center justify-between">
                                 <div className="flex items-center space-x-3">
                                     <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                     <span className="text-xs font-bold text-zinc-900 italic">Organic Discovery</span>
                                 </div>
                                 <button className="p-2 hover:bg-gray-50 rounded-xl transition-all">
                                     <Share2 className="w-4 h-4 text-gray-400" />
                                 </button>
                             </div>
                         </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
