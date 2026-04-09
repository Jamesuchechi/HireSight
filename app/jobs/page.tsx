"use client";

import { useEffect, useState, useTransition, Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { Database } from "@/types/database";
import CandidateJobCard from "@/components/jobs/CandidateJobCard";
import { 
    Search, Filter, MapPin, Briefcase, DollarSign, 
    Zap, Sparkles, SlidersHorizontal, ChevronDown, 
    X, LayoutGrid, List as ListIcon, Loader2 
} from "lucide-react";
import { useQueryState, parseAsArrayOf, parseAsString, parseAsInteger } from "nuqs";
import { motion, AnimatePresence } from "framer-motion";
import DashboardLayout from "@/components/DashboardLayout";

type Job = Database["public"]["Tables"]["jobs"]["Row"] & {
    profiles: {
        full_name: string | null;
        avatar_url: string | null;
    } | null;
};

function JobDiscoveryContent() {
    const supabase = createClient();
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [isPending, startTransition] = useTransition();

    // nuqs URL state management
    const [q, setQ] = useQueryState("q", { defaultValue: "" });
    const [remoteType, setRemoteType] = useQueryState("remote", parseAsArrayOf(parseAsString).withDefault([]));
    const [expLevel, setExpLevel] = useQueryState("exp", parseAsArrayOf(parseAsString).withDefault([]));
    const [jobType, setJobType] = useQueryState("type", parseAsArrayOf(parseAsString).withDefault([]));
    const [minSalary, setMinSalary] = useQueryState("salary", parseAsInteger.withDefault(0));
    const [radius, setRadius] = useQueryState("radius", parseAsInteger.withDefault(50));

    useEffect(() => {
        const fetchJobs = async () => {
            setLoading(true);
            let query = supabase
                .from("jobs")
                .select("*, profiles!company_id(full_name, avatar_url)")
                .eq("status", "active");

            if (q) {
                query = query.or(`title.ilike.%${q}%,description.ilike.%${q}%`);
            }

            if (remoteType.length > 0) {
                query = query.in("remote_type", remoteType);
            }

            if (expLevel.length > 0) {
                query = query.in("experience_level", expLevel);
            }

            if (jobType.length > 0) {
                query = query.in("job_type", jobType);
            }

            if (minSalary > 0) {
                query = query.gte("salary_min", minSalary);
            }

            const { data, error } = await query.order("created_at", { ascending: false });

            if (!error && data) {
                setJobs(data);
            }
            setLoading(false);
        };

        fetchJobs();
    }, [supabase, q, remoteType, expLevel, jobType, minSalary]);

    const clearFilters = () => {
        setQ("");
        setRemoteType([]);
        setExpLevel([]);
        setJobType([]);
        setMinSalary(0);
        setRadius(50);
    };

    const hasFilters = q || remoteType.length > 0 || expLevel.length > 0 || jobType.length > 0 || minSalary > 0;

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-gray-50/30">
                {/* Discovery Header */}
                <header className="bg-white border-b border-gray-100 py-12 px-6 rounded-[40px] mb-12 shadow-sm">
                    <div className="max-w-7xl mx-auto space-y-8">
                        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                            <div className="space-y-2">
                                <div className="flex items-center space-x-2">
                                    <Sparkles className="w-4 h-4 text-primary animate-pulse" />
                                    <span className="text-[10px] font-black text-primary uppercase tracking-widest italic">AI Discovery Protocol</span>
                                </div>
                                <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                                    Infinite <span className="text-primary tracking-normal">Opportunities</span>
                                </h1>
                                <p className="text-gray-500 font-bold">Scanning <span className="text-primary italic font-black">{jobs.length} relevant</span> positions matching your neural profile.</p>
                            </div>
                        </div>

                        {/* Integrated Search Bar */}
                        <div className="max-w-4xl flex flex-col md:flex-row gap-4">
                            <div className="relative flex-[2] group">
                                <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-primary transition-colors" />
                                <input 
                                    type="text"
                                    placeholder="Search by title, keywords, or company..."
                                    value={q}
                                    onChange={(e) => setQ(e.target.value)}
                                    className="w-full pl-16 pr-6 py-5 bg-gray-50/50 border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 focus:bg-white transition-all shadow-sm"
                                />
                            </div>
                            <div className="relative flex-1 group">
                                <MapPin className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-primary transition-colors" />
                                <input 
                                    type="text"
                                    placeholder="Location..."
                                    className="w-full pl-16 pr-6 py-5 bg-gray-50/50 border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 focus:bg-white transition-all shadow-sm"
                                />
                            </div>
                            <button className="px-10 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-sm uppercase tracking-widest italic shadow-2xl hover:scale-[1.05] active:scale-[0.95] transition-all flex items-center space-x-2">
                                <span>Execute</span>
                                <Zap className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-12 pt-4">
                    
                    {/* Filters Sidebar */}
                    <aside className="lg:col-span-1 space-y-10">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-xl font-black font-display text-zinc-900 italic tracking-tight uppercase">Filters</h3>
                            {hasFilters && (
                                <button 
                                    onClick={clearFilters}
                                    className="text-[10px] font-black text-primary uppercase tracking-widest hover:underline"
                                >
                                    Clear Protocol
                                </button>
                            )}
                        </div>

                        {/* Remote Type */}
                        <div className="space-y-4">
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Work Protocol</p>
                            <div className="flex flex-col space-y-3">
                                {["remote", "hybrid", "onsite"].map((type) => (
                                    <label key={type} className="flex items-center space-x-3 group cursor-pointer">
                                        <div className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all ${
                                            remoteType.includes(type) ? "bg-primary border-primary" : "border-gray-200 group-hover:border-primary/50"
                                        }`}>
                                            {remoteType.includes(type) && <div className="w-2 h-2 bg-white rounded-full" />}
                                        </div>
                                        <input 
                                            type="checkbox" 
                                            className="hidden" 
                                            checked={remoteType.includes(type)}
                                            onChange={(e) => {
                                                const next = e.target.checked 
                                                    ? [...remoteType, type] 
                                                    : remoteType.filter(t => t !== type);
                                                setRemoteType(next);
                                            }}
                                        />
                                        <span className={`text-xs font-bold uppercase tracking-wider ${remoteType.includes(type) ? "text-primary" : "text-gray-500"}`}>
                                            {type}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Experience Level */}
                        <div className="space-y-4">
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Scalar Level</p>
                             <div className="flex flex-col space-y-3">
                                {["entry", "mid", "senior", "lead", "executive"].map((lvl) => (
                                    <label key={lvl} className="flex items-center space-x-3 group cursor-pointer">
                                        <div className={`w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all ${
                                            expLevel.includes(lvl) ? "bg-primary border-primary" : "border-gray-200 group-hover:border-primary/50"
                                        }`}>
                                            {expLevel.includes(lvl) && <div className="w-2 h-2 bg-white rounded-full" />}
                                        </div>
                                        <input 
                                            type="checkbox" 
                                            className="hidden" 
                                            checked={expLevel.includes(lvl)}
                                            onChange={(e) => {
                                                const next = e.target.checked 
                                                    ? [...expLevel, lvl] 
                                                    : expLevel.filter(t => t !== lvl);
                                                setExpLevel(next);
                                            }}
                                        />
                                        <span className={`text-xs font-bold uppercase tracking-wider ${expLevel.includes(lvl) ? "text-primary" : "text-gray-500"}`}>
                                            {lvl}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {/* Salary Range */}
                        <div className="space-y-4">
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Min Compensation</p>
                            <div className="space-y-4">
                                <input 
                                    type="range" 
                                    min="0" 
                                    max="250000" 
                                    step="10000"
                                    value={minSalary}
                                    onChange={(e) => setMinSalary(parseInt(e.target.value))}
                                    className="w-full accent-primary"
                                />
                                <div className="flex justify-between text-[10px] font-black text-primary uppercase">
                                    <span>$0</span>
                                    <span>${(minSalary / 1000).toFixed(0)}k+</span>
                                </div>
                            </div>
                        </div>

                        {/* Radius Search */}
                        <div className="space-y-4">
                            <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Search Radius</p>
                             <div className="space-y-4">
                                <input 
                                    type="range" 
                                    min="5" 
                                    max="500" 
                                    step="5"
                                    value={radius}
                                    onChange={(e) => setRadius(parseInt(e.target.value))}
                                    className="w-full accent-secondary"
                                />
                                <div className="flex justify-between text-[10px] font-black text-secondary uppercase">
                                    <span>5mi</span>
                                    <span>{radius}mi</span>
                                </div>
                            </div>
                        </div>
                    </aside>

                    {/* Jobs Feed */}
                    <div className="lg:col-span-3 space-y-8">
                        {/* Feed Controls */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <button className="p-2 bg-white border border-gray-100 rounded-xl text-primary shadow-sm shadow-primary/5">
                                    <LayoutGrid className="w-5 h-5" />
                                </button>
                                <button className="p-2 text-gray-400 hover:text-primary transition-colors">
                                    <ListIcon className="w-5 h-5" />
                                </button>
                            </div>
                            <div className="flex items-center space-x-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
                                <span>Sort By:</span>
                                <button className="flex items-center space-x-1 text-zinc-900 group">
                                    <span>Relevance</span>
                                    <ChevronDown className="w-3 h-3 group-hover:translate-y-0.5 transition-transform" />
                                </button>
                            </div>
                        </div>

                        {loading ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {[1, 2, 3, 4, 5, 6].map(i => (
                                    <div key={i} className="h-64 bg-white border border-gray-100 rounded-[32px] animate-pulse" />
                                ))}
                            </div>
                        ) : jobs.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                {jobs.map(job => (
                                    <CandidateJobCard key={job.id} job={job} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white border-2 border-dashed border-gray-100 rounded-[48px] p-24 text-center space-y-6">
                                <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto">
                                    <Search className="w-12 h-12 text-gray-300" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-3xl font-black text-zinc-900 italic tracking-tight">Zero Matches Detected</h3>
                                    <p className="text-gray-500 font-bold max-w-sm mx-auto">
                                        We couldn't find any opportunities matching your current protocol. Try broadening your filter parameters.
                                    </p>
                                </div>
                                <button 
                                    onClick={clearFilters}
                                    className="px-10 py-4 bg-primary text-white rounded-2xl font-black text-xs uppercase tracking-widest italic shadow-xl shadow-primary/20 hover:scale-105 transition-all"
                                >
                                    Reset Discovery Matrix
                                </button>
                            </div>
                        )}
                        
                        <div className="pt-10 flex justify-center">
                             <button className="px-12 py-5 bg-white border border-gray-100 rounded-[32px] font-black text-xs uppercase tracking-widest italic text-gray-400 hover:text-zinc-900 hover:shadow-xl transition-all">
                                Load More Protocols
                             </button>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

export default function JobDiscoveryPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-gray-50/30">
                <Loader2 className="w-10 h-10 animate-spin text-primary" />
            </div>
        }>
            <JobDiscoveryContent />
        </Suspense>
    );
}
