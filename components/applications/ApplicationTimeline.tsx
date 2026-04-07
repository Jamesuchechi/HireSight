"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { formatDistanceToNow } from "date-fns";
import { 
  Clock, CheckCircle2, XCircle, MousePointer2, 
  TrendingUp, FileText, User, MessageSquare
} from "lucide-react";
import { motion } from "framer-motion";

interface StatusHistory {
  id: string;
  old_status: string | null;
  new_status: string;
  reason: string | null;
  created_at: string;
  changed_by_profile?: {
    full_name: string;
  };
}

export default function ApplicationTimeline({ applicationId }: { applicationId: string }) {
  const supabase = createClient();
  const [history, setHistory] = useState<StatusHistory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      const { data, error } = await supabase
        .from("application_status_history")
        .select(`
          *,
          changed_by_profile:profiles!changed_by(full_name)
        `)
        .eq("application_id", applicationId)
        .order("created_at", { ascending: false });

      if (data) setHistory(data as any);
      setLoading(false);
    };

    fetchHistory();
  }, [applicationId, supabase]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "applied": return <Clock className="w-4 h-4" />;
      case "screening": return <MousePointer2 className="w-4 h-4" />;
      case "interview": return <TrendingUp className="w-4 h-4" />;
      case "hired": return <CheckCircle2 className="w-4 h-4" />;
      case "rejected": return <XCircle className="w-4 h-4" />;
      default: return <FileText className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "applied": return "bg-blue-50 text-blue-500 border-blue-100";
      case "screening": return "bg-primary/10 text-primary border-primary/20";
      case "interview": return "bg-secondary/10 text-secondary border-secondary/20";
      case "hired": return "bg-emerald-50 text-emerald-500 border-emerald-100";
      case "rejected": return "bg-rose-50 text-rose-500 border-rose-100";
      default: return "bg-gray-50 text-gray-500 border-gray-100";
    }
  };

  if (loading) return (
    <div className="flex justify-center p-8">
      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-8 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-100">
      {history.map((event, idx) => (
        <motion.div 
          key={event.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="relative flex items-start space-x-6 pl-10"
        >
          <div className={`absolute left-0 w-10 h-10 rounded-full border-4 border-white flex items-center justify-center shadow-sm z-10 ${getStatusColor(event.new_status)}`}>
            {getStatusIcon(event.new_status)}
          </div>
          
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">
                Status Updated to <span className="text-primary">{event.new_status}</span>
              </h4>
              <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                {formatDistanceToNow(new Date(event.created_at))} ago
              </span>
            </div>
            
            {event.reason && (
              <p className="text-sm text-gray-500 leading-relaxed font-bold bg-gray-50/50 p-4 rounded-2xl border border-gray-100">
                "{event.reason}"
              </p>
            )}

            <div className="flex items-center space-x-2 text-[10px] font-black text-gray-400 uppercase tracking-widest">
              <User className="w-3 h-3" />
              <span>{event.changed_by_profile?.full_name || "System Protocol"}</span>
            </div>
          </div>
        </motion.div>
      ))}

      {history.length === 0 && (
        <div className="text-center py-10">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">No activity history recorded yet.</p>
        </div>
      )}
    </div>
  );
}
