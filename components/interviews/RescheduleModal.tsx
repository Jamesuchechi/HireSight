"use client";

import { useState } from "react";
import { 
    Calendar, Clock, MessageSquare, 
    X, Send, Loader2, AlertCircle,
    ChevronRight, ArrowRight
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import { createClient } from "@/lib/supabase/client";
import { notify } from "@/lib/notifications/notify";

interface RescheduleModalProps {
    isOpen: boolean;
    onClose: () => void;
    interview: any;
    onComplete: () => void;
}

export default function RescheduleModal({ isOpen, onClose, interview, onComplete }: RescheduleModalProps) {
    const supabase = createClient();
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState({
        date: format(new Date(), "yyyy-MM-dd"),
        time: "10:00",
        reason: ""
    });

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const proposedAt = new Date(`${form.date}T${form.time}:00`).toISOString();
            
            // 1. Update Interview status and proposed times
            const newProposal = {
                date: proposedAt,
                reason: form.reason,
                proposed_at: new Date().toISOString()
            };

            const updatedProposals = [...(interview.proposed_times || []), newProposal];

            const { error } = await supabase
                .from("interviews")
                .update({ 
                    candidate_response: 'proposed_reschedule',
                    proposed_times: updatedProposals
                })
                .eq("id", interview.id);

            if (error) throw error;

            // 2. Notify Recruiter (Primary Participant)
            const interviewer = interview.participants.find((p: any) => p.role === 'interviewer');
            if (interviewer) {
                await notify(interviewer.profile_id, {
                    title: "Reschedule Protocol Requested",
                    message: `Candidate has proposed a new tactical window for the ${interview.type} session. View mission details to review.`,
                    type: "interview_rescheduled",
                    action_url: `/dashboard/interviews`,
                    action_text: "Review Proposal"
                });
            }

            onComplete();
            onClose();
        } catch (error) {
            console.error("Reschedule Failed:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-black/80 backdrop-blur-xl"
                    />

                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-xl bg-white rounded-[48px] shadow-2xl overflow-hidden"
                    >
                        <div className="p-12 space-y-10">
                            <header className="flex items-center justify-between">
                                <div className="space-y-1">
                                    <h3 className="text-3xl font-black text-zinc-900 italic tracking-tighter uppercase leading-none">Propose <span className="text-primary">Conflict</span></h3>
                                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none">Tactical Window Re-alignment</p>
                                </div>
                                <button onClick={onClose} className="p-3 bg-gray-50 rounded-2xl text-gray-400 hover:text-red-500 transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </header>

                            <div className="space-y-8">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-4">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                            <Calendar className="w-3 h-3 text-primary" />
                                            <span>Target Date</span>
                                        </label>
                                        <input 
                                            type="date" 
                                            value={form.date}
                                            onChange={(e) => setForm({...form, date: e.target.value})}
                                            className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all text-zinc-900"
                                        />
                                    </div>
                                    <div className="space-y-4">
                                        <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                            <Clock className="w-3 h-3 text-primary" />
                                            <span>Target Time</span>
                                        </label>
                                        <input 
                                            type="time" 
                                            value={form.time}
                                            onChange={(e) => setForm({...form, time: e.target.value})}
                                            className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all text-zinc-900"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4 flex items-center space-x-2">
                                        <MessageSquare className="w-3 h-3 text-primary" />
                                        <span>Conflict Manifest</span>
                                    </label>
                                    <textarea 
                                        placeholder="Reason for realignment protocol..."
                                        value={form.reason}
                                        onChange={(e) => setForm({...form, reason: e.target.value})}
                                        className="w-full px-8 py-6 bg-gray-50 border border-gray-100 rounded-[32px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/10 transition-all h-32 resize-none text-zinc-900 italic"
                                    />
                                </div>

                                <div className="p-6 bg-amber-500/5 rounded-3xl border border-amber-500/10 flex items-start space-x-4">
                                    <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                                    <p className="text-[10px] font-bold text-amber-600 italic leading-relaxed">
                                        Submitting this proposal will temporarily halt the current protocol until a recruiter reviews and confirms the new window.
                                    </p>
                                </div>

                                <button 
                                    onClick={handleSubmit}
                                    disabled={loading || !form.reason}
                                    className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-[10px] uppercase tracking-[0.3em] italic hover:bg-primary transition-all shadow-2xl flex items-center justify-center space-x-3 disabled:opacity-30 group"
                                >
                                    {loading ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                    ) : (
                                        <>
                                            <span>Deploy Proposal</span>
                                            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
