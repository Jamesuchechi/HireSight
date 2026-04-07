"use client";

import { MapPin, Briefcase, DollarSign, Star, Zap, Share2, ArrowRight } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Database } from "@/types/database";
import Link from "next/link";
import { motion } from "framer-motion";

type Job = Database["public"]["Tables"]["jobs"]["Row"] & {
  profiles: {
    full_name: string | null;
    avatar_url: string | null;
  } | null;
};

interface CandidateJobCardProps {
  job: Job;
  isSaved?: boolean;
  onSave?: (id: string) => void;
  onShare?: (id: string) => void;
  matchScore?: number;
}

export default function CandidateJobCard({
  job,
  isSaved = false,
  onSave,
  onShare,
  matchScore = 85, // Default for demo/logic
}: CandidateJobCardProps) {
  return (
    <div className="group relative bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden">
      {/* Top Banner: Match Score */}
      <div className="absolute top-0 right-0 p-6 flex flex-col items-end">
        <div className="flex items-center space-x-2 bg-primary/5 px-3 py-1.5 rounded-full border border-primary/10">
          <Zap className="w-3 h-3 text-primary animate-pulse" />
          <span className="text-[10px] font-black text-primary uppercase tracking-widest">{matchScore}% Match</span>
        </div>
      </div>

      <div className="flex flex-col h-full">
        {/* Company Info */}
        <div className="flex items-center space-x-4 mb-6">
          <div className="w-12 h-12 bg-gray-50 rounded-2xl flex items-center justify-center border border-gray-100 group-hover:scale-110 transition-transform overflow-hidden font-black text-primary relative">
             {job.profiles?.avatar_url ? (
               <img src={job.profiles.avatar_url} alt={job.profiles.full_name || ""} className="w-full h-full object-cover" />
             ) : (
               <span className="text-lg italic">{(job.profiles?.full_name || job.title).substring(0, 1).toUpperCase()}</span>
             )}
          </div>
          <div>
            <h4 className="text-sm font-black text-zinc-900 italic uppercase tracking-tight line-clamp-1">
              {job.profiles?.full_name || "Enterprise Partner"}
            </h4>
            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">{job.location || "Remote Protocol"}</p>
          </div>
        </div>

        {/* Job Title */}
        <div className="mb-6">
          <h3 className="text-xl font-black text-zinc-900 italic tracking-tight group-hover:text-primary transition-colors mb-4 line-clamp-2 min-h-[3.5rem]">
            {job.title}
          </h3>
          
          <div className="flex flex-wrap gap-4 items-center text-xs text-gray-500 font-bold">
            <div className="flex items-center space-x-1.5 bg-gray-50 px-3 py-1.5 rounded-xl border border-gray-100">
              <MapPin className="w-3 h-3 text-primary" />
              <span>{job.location || "Remote"}</span>
            </div>
            <div className="flex items-center space-x-1.5 bg-gray-50 px-3 py-1.5 rounded-xl border border-gray-100">
              <Briefcase className="w-3 h-3 text-primary" />
              <span className="capitalize">{job.job_type}</span>
            </div>
            {job.salary_min && (
              <div className="flex items-center space-x-1.5 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-100 text-emerald-600">
                <DollarSign className="w-3 h-3" />
                <span>${(job.salary_min / 1000).toFixed(0)}k - ${(job.salary_max! / 1000).toFixed(0)}k</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between mt-auto pt-6 border-t border-gray-50">
          <Link
            href={`/jobs/${job.id}`}
             className="inline-flex items-center space-x-3 px-6 py-3 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest italic shadow-xl hover:bg-primary transition-all group/btn"
          >
            <span>View Protocol</span>
            <ArrowRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
          </Link>

          <div className="flex items-center space-x-2">
            <button
               onClick={(e) => { e.preventDefault(); onShare?.(job.id); }}
               className="p-3 text-gray-400 hover:bg-gray-50 hover:text-primary rounded-xl transition-all"
            >
              <Share2 className="w-4 h-4" />
            </button>
            <button
               onClick={(e) => { e.preventDefault(); onSave?.(job.id); }}
               className={`p-3 rounded-xl transition-all ${
                 isSaved ? "bg-primary/10 text-primary" : "text-gray-400 hover:bg-gray-50 hover:text-primary"
               }`}
            >
              <Star className={`w-4 h-4 ${isSaved ? "fill-primary" : ""}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Expiration Label */}
      <div className="absolute left-6 top-6">
         <div className="flex items-center space-x-1.5">
           <div className="w-1.5 h-1.5 rounded-full bg-primary" />
           <p className="text-[8px] font-black uppercase tracking-widest text-gray-400">posted {formatDistanceToNow(new Date(job.created_at))} ago</p>
         </div>
      </div>

      {/* Decorative Accent */}
      <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-secondary/5 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700 pointer-events-none" />
    </div>
  );
}
