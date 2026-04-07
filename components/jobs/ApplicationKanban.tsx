"use client";

import { motion, AnimatePresence } from "framer-motion";
import { 
    Users, MousePointer2, TrendingUp, 
    CheckCircle2, XCircle, MoreVertical, 
    Zap, Clock, FileText 
} from "lucide-react";
import { Database } from "@/types/database";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

type Application = any; // Will be properly typed in the page

const STAGES = [
    { id: "applied", label: "New Metrics", color: "bg-blue-500" },
    { id: "screening", label: "Vetting", color: "bg-primary" },
    { id: "interview", label: "Protocol Match", color: "bg-secondary" },
    { id: "offer", label: "Offer Phase", color: "bg-emerald-500" },
    { id: "hired", label: "Successful Hires", color: "bg-emerald-600" },
    { id: "rejected", label: "Aborted", color: "bg-red-500" }
];

interface KanbanProps {
    applications: Application[];
    onMove: (id: string, nextStatus: string) => void;
}

export default function ApplicationKanban({ applications, onMove }: KanbanProps) {
    const getAppsInStage = (stage: string) => applications.filter(app => app.status === stage);

    return (
        <div className="flex space-x-6 overflow-x-auto pb-12 scrollbar-hide min-h-[600px]">
            {STAGES.map(stage => (
                <div key={stage.id} className="w-[320px] min-w-[320px] flex flex-col space-y-6">
                    {/* Stage Header */}
                    <div className="flex items-center justify-between px-2">
                        <div className="flex items-center space-x-3">
                             <div className={`w-2.5 h-2.5 rounded-full ${stage.color} shadow-[0_0_8px_rgba(0,0,0,0.1)]`} />
                             <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400">{stage.label}</h3>
                             <div className="bg-gray-100 text-gray-500 px-2 py-0.5 rounded-md text-[10px] font-black">
                                 {getAppsInStage(stage.id).length}
                             </div>
                        </div>
                    </div>

                    {/* Stage Lane */}
                    <div className="flex-grow bg-gray-50/50 rounded-[40px] p-3 border border-gray-100/50 space-y-4">
                        <AnimatePresence>
                             {getAppsInStage(stage.id).map(app => (
                                 <KanbanCard 
                                    key={app.id} 
                                    app={app} 
                                    onMove={(next) => onMove(app.id, next)}
                                 />
                             ))}
                        </AnimatePresence>
                        {getAppsInStage(stage.id).length === 0 && (
                            <div className="h-20 flex items-center justify-center border-2 border-dashed border-gray-100 rounded-3xl">
                                <span className="text-[8px] font-black uppercase tracking-widest text-gray-300 italic">Empty Protocol</span>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}

function KanbanCard({ app, onMove }: { app: any, onMove: (next: string) => void }) {
    return (
        <motion.div
            layoutId={app.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="group block bg-white border border-gray-100 rounded-[28px] p-5 shadow-sm hover:shadow-xl hover:border-primary/20 transition-all cursor-grab active:cursor-grabbing"
        >
            <div className="space-y-4">
                <div className="flex items-start justify-between">
                    <div className="flex items-center space-x-3">
                         <div className="w-10 h-10 bg-gray-50 rounded-xl border border-gray-100 flex items-center justify-center font-black text-primary italic overflow-hidden">
                             {app.candidate?.avatar_url ? (
                                 <img src={app.candidate.avatar_url} className="w-full h-full object-cover" />
                             ) : (
                                 <span>{app.candidate?.full_name?.[0] || 'U'}</span>
                             )}
                         </div>
                         <div>
                            <h4 className="text-sm font-black text-zinc-900 line-clamp-1 italic">{app.candidate?.full_name}</h4>
                            <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic">{formatDistanceToNow(new Date(app.created_at))} ago</p>
                         </div>
                    </div>
                    <div className="flex flex-col items-end space-y-1">
                         <div className="flex items-center space-x-1 text-primary">
                             <Zap className="w-3 h-3 animate-pulse" />
                             <span className="text-[10px] font-black">{app.match_score || 85}%</span>
                         </div>
                    </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-50">
                    <div className="flex -space-x-1">
                        <Link 
                            href={`/dashboard/applications/review/${app.id}`}
                            className="p-2 bg-gray-50 text-gray-400 hover:bg-primary hover:text-white rounded-xl transition-all"
                            title="Review Details"
                        >
                            <FileText className="w-3.5 h-3.5" />
                        </Link>
                    </div>

                    <div className="flex items-center space-x-1">
                         {STAGES.filter(s => s.id !== app.status).slice(0, 2).map(s => (
                             <button
                                key={s.id}
                                onClick={() => onMove(s.id)}
                                className="text-[8px] font-black uppercase tracking-widest text-primary hover:underline"
                             >
                                {s.label.split(' ')[0]}
                             </button>
                         ))}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}
