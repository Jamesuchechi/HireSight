"use client";

import { MoreVertical, Users, Eye, Edit2, Copy, Trash2, Clock, MapPin, Briefcase, Star, DollarSign, TrendingUp } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Database } from "@/types/database";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type Job = Database["public"]["Tables"]["jobs"]["Row"];

interface RecruiterJobCardProps {
  job: Job;
  applicantCount: number;
  viewCount: number;
  onEdit?: (id: string) => void;
  onDuplicate?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export default function RecruiterJobCard({
  job,
  applicantCount,
  viewCount,
  onEdit,
  onDuplicate,
  onDelete,
}: RecruiterJobCardProps) {
  const [showMenu, setShowMenu] = useState(false);

  const statusColors = {
    active: "bg-emerald-500",
    draft: "bg-amber-500",
    closed: "bg-rose-500",
    deleted: "bg-gray-400",
  };

  return (
    <div className="group relative bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm hover:shadow-xl transition-all duration-500 overflow-hidden">
      {/* Featured Badge */}
      {job.is_featured && (
        <div className="absolute top-0 left-0 px-4 py-1.5 bg-primary text-white text-[8px] font-black uppercase tracking-[0.2em] rounded-br-2xl flex items-center space-x-1.5 z-10 shadow-lg shadow-primary/20">
          <Star className="w-3 h-3 fill-white" />
          <span>Featured Priority</span>
        </div>
      )}

      {/* Status Badge */}
      <div className="absolute top-6 right-6 flex items-center space-x-2">
        <div className={`w-2 h-2 rounded-full ${statusColors[job.status as keyof typeof statusColors]} animate-pulse`} />
        <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">
          {job.status}
        </span>
      </div>

      <div className="flex flex-col h-full pt-4">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center space-x-2 mb-2">
            {job.department && (
              <span className="px-2 py-0.5 bg-gray-50 text-gray-400 text-[8px] font-black uppercase tracking-widest border border-gray-100 rounded-lg">
                {job.department}
              </span>
            )}
          </div>
          <h3 className="text-xl font-black text-zinc-900 italic tracking-tight group-hover:text-primary transition-colors mb-2">
            {job.title}
          </h3>
          <div className="flex flex-wrap gap-4 items-center text-xs text-gray-500 font-bold">
            <div className="flex items-center space-x-1">
              <MapPin className="w-3 h-3 text-primary" />
              <span>{job.location || "Remote"}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Briefcase className="w-3 h-3 text-primary" />
              <span>{job.job_type}</span>
            </div>
          </div>
          {job.salary_min && (
            <div className="mt-3 flex items-center space-x-1.5 text-emerald-600">
              <DollarSign className="w-3.5 h-3.5" />
              <span className="text-sm font-black italic tracking-tight">
                {job.currency} {(job.salary_min / 1000).toFixed(0)}k - {(job.salary_max ? job.salary_max / 1000 : 0).toFixed(0)}k
              </span>
              <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest ml-1">/ {job.salary_period}</span>
            </div>
          )}
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 mt-auto pt-6 border-t border-gray-50">
          <div className="flex flex-col items-center p-3 bg-primary/5 rounded-2xl">
            <p className="text-lg font-black text-primary italic leading-none">{applicantCount}</p>
            <p className="text-[7px] font-black text-gray-400 uppercase tracking-widest mt-1">Applicants</p>
          </div>
          <div className="flex flex-col items-center p-3 bg-secondary/5 rounded-2xl">
            <p className="text-lg font-black text-secondary italic leading-none">{viewCount}</p>
            <p className="text-[7px] font-black text-gray-400 uppercase tracking-widest mt-1">Views</p>
          </div>
          <div className="flex flex-col items-center p-3 bg-emerald-50 rounded-2xl">
            <p className="text-lg font-black text-emerald-600 italic leading-none">
              {viewCount > 0 ? ((applicantCount / viewCount) * 100).toFixed(0) : 0}%
            </p>
            <p className="text-[7px] font-black text-gray-400 uppercase tracking-widest mt-1">Rate</p>
          </div>
        </div>

        {/* Main Action Button */}
        <div className="mt-8">
           <button 
             onClick={() => window.location.href = `/dashboard/jobs/${job.id}/applicants`}
             className="w-full py-4 bg-zinc-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic flex items-center justify-center space-x-2 hover:bg-primary transition-all shadow-lg active:scale-95"
           >
             <Users className="w-4 h-4" />
             <span>Monitor Applicants</span>
           </button>
        </div>

        {/* Actions Menu */}
        <div className="absolute top-6 right-20">
          <div className="relative">
            <button 
              onClick={() => setShowMenu(!showMenu)}
              className="p-2 hover:bg-gray-50 rounded-xl transition-all"
            >
              <MoreVertical className="w-5 h-5 text-gray-400" />
            </button>

            <AnimatePresence>
              {showMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowMenu(false)} 
                  />
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: 10 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: 10 }}
                    className="absolute right-0 top-full mt-2 w-48 bg-white border border-gray-100 rounded-2xl shadow-2xl z-20 py-2 overflow-hidden"
                  >
                    <button
                      onClick={() => { window.location.href = `/dashboard/jobs/${job.id}/analytics`; setShowMenu(false); }}
                      className="w-full px-4 py-2.5 text-left flex items-center space-x-3 hover:bg-gray-50 transition-all group/item"
                    >
                      <TrendingUp className="w-4 h-4 text-gray-400 group-hover/item:text-primary" />
                      <span className="text-xs font-bold text-gray-600 group-hover/item:text-zinc-900">Deep Intel (Analytics)</span>
                    </button>
                    <button
                      onClick={() => { window.location.href = `/dashboard/jobs/${job.id}/applicants`; setShowMenu(false); }}
                      className="w-full px-4 py-2.5 text-left flex items-center space-x-3 hover:bg-gray-50 transition-all group/item"
                    >
                      <Users className="w-4 h-4 text-gray-400 group-hover/item:text-primary" />
                      <span className="text-xs font-bold text-gray-600 group-hover/item:text-zinc-900">View Pipeline</span>
                    </button>
                    <button
                      onClick={() => { onEdit?.(job.id); setShowMenu(false); }}
                      className="w-full px-4 py-2.5 text-left flex items-center space-x-3 hover:bg-gray-50 transition-all group/item"
                    >
                      <Edit2 className="w-4 h-4 text-gray-400 group-hover/item:text-primary" />
                      <span className="text-xs font-bold text-gray-600 group-hover/item:text-zinc-900">Edit Posting</span>
                    </button>
                    <button
                      onClick={() => { onDuplicate?.(job.id); setShowMenu(false); }}
                      className="w-full px-4 py-2.5 text-left flex items-center space-x-3 hover:bg-gray-50 transition-all group/item"
                    >
                      <Copy className="w-4 h-4 text-gray-400 group-hover/item:text-secondary" />
                      <span className="text-xs font-bold text-gray-600 group-hover/item:text-zinc-900">Duplicate</span>
                    </button>
                    <div className="h-px bg-gray-100 my-1 mx-2" />
                    <button
                      onClick={() => { onDelete?.(job.id); setShowMenu(false); }}
                      className="w-full px-4 py-2.5 text-left flex items-center space-x-3 hover:bg-rose-50 transition-all group/item"
                    >
                      <Trash2 className="w-4 h-4 text-rose-400" />
                      <span className="text-xs font-bold text-rose-600">Delete Permanently</span>
                    </button>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Hover Background Accent */}
      <div className="absolute -left-10 -bottom-10 w-40 h-40 bg-primary/5 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700 pointer-events-none" />
    </div>
  );
}
