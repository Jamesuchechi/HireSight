"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    XCircle, Send, Calendar, Clock, 
    User, Briefcase, Search, ChevronDown
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { format } from "date-fns";
import { notify } from "@/lib/notifications/notify";

interface ScheduleInterviewModalProps {
    isOpen: boolean;
    onClose: () => void;
    applicationId?: string; // Optional context
    onComplete?: () => void;
}

export default function ScheduleInterviewModal({ 
    isOpen, 
    onClose, 
    applicationId,
    onComplete 
}: ScheduleInterviewModalProps) {
    const supabase = createClient();
    const [isSaving, setIsSaving] = useState(false);
    const [applications, setApplications] = useState<any[]>([]);
    const [selectedApplicationId, setSelectedApplicationId] = useState<string | null>(applicationId || null);
    const [searchQuery, setSearchQuery] = useState("");
    const [isSelectingApplication, setIsSelectingApplication] = useState(!applicationId);

    const [scheduleForm, setScheduleForm] = useState({
        date: format(new Date(), "yyyy-MM-dd"),
        time: "10:00",
        duration: 60,
        type: "technical",
        location: "Remote",
        notes: "",
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });

    useEffect(() => {
        if (isOpen && !applicationId) {
            fetchApplications();
        }
    }, [isOpen, applicationId]);

    const fetchApplications = async () => {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data } = await supabase
            .from("job_applications")
            .select(`
                id,
                status,
                candidate:profiles!candidate_id(id, full_name, avatar_url),
                job:jobs(id, title)
            `)
            .eq("job.company_id", user.id)
            .in("status", ["applied", "screening", "interview"])
            .order("created_at", { ascending: false });

        if (data) setApplications(data);
    };

    const handleSchedule = async () => {
        const appId = applicationId || selectedApplicationId;
        if (!appId) return;

        setIsSaving(true);
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const scheduledAt = new Date(`${scheduleForm.date}T${scheduleForm.time}:00`).toISOString();

        console.log("Data Payload for Interview:", {
            application_id: appId,
            type: scheduleForm.type,
            status: "scheduled",
            scheduled_at: scheduledAt,
            duration_minutes: Number(scheduleForm.duration),
            location: scheduleForm.location,
            candidate_instructions: scheduleForm.notes,
            timezone: scheduleForm.timezone,
            created_by: user.id
        });

        // 1. Create Interview
        const { data: interview, error: intError } = await supabase
            .from("interviews")
            .insert({
                application_id: appId,
                type: scheduleForm.type,
                status: "scheduled",
                scheduled_at: scheduledAt,
                duration_minutes: Number(scheduleForm.duration),
                location: scheduleForm.location,
                candidate_instructions: scheduleForm.notes,
                timezone: scheduleForm.timezone,
                created_by: user.id
            })
            .select(`
                id,
                application_id,
                job_application:job_applications(
                    candidate_id
                )
            `)
            .single();

        if (intError) {
            console.error("Interview Creation Failed:", JSON.stringify({
                message: intError.message,
                details: intError.details,
                hint: intError.hint,
                code: intError.code
            }, null, 2));
            setIsSaving(false);
            return;
        }

        if (!interview) {
            console.error("Interview Creation succeeded but no data was returned. This may be an RLS issue.");
            setIsSaving(false);
            return;
        }

        console.log("INTERVIEW CREATION SUCCESS:", interview.id);

        // 2. Add Participants (Recruiter + Candidate)
        await supabase.from("interview_participants").insert([
            { interview_id: interview.id, profile_id: user.id, role: "interviewer", is_primary: true },
            { interview_id: interview.id, profile_id: (interview.job_application as any).candidate_id, role: "candidate" }
        ]);

        // 3. Update Application Status to 'interview'
        await supabase
            .from("job_applications")
            .update({ status: "interview" })
            .eq("id", appId);

        setIsSaving(false);
        
        // Notify candidate
        await notify((interview.job_application as any).candidate_id, {
            title: "Interview Scheduled",
            message: `A new ${scheduleForm.type} protocol has been scheduled for ${scheduleForm.date} at ${scheduleForm.time}.`,
            type: "interview_scheduled"
        });

        if (onComplete) onComplete();
        onClose();
    };

    const filteredApplications = applications.filter(app => 
        app.candidate.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        app.job.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const selectedApp = applicationId 
        ? null // Not needed if provided via props
        : applications.find(a => a.id === selectedApplicationId);

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 text-zinc-900">
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="absolute inset-0 bg-zinc-900/60 backdrop-blur-md"
                    />
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-2xl bg-white rounded-[40px] shadow-2xl overflow-hidden max-h-[90vh] flex flex-col"
                    >
                        <div className="p-10 space-y-8 overflow-y-auto scrollbar-hide">
                            <div className="flex items-center justify-between">
                                <div className="space-y-1">
                                     <h3 className="text-3xl font-black text-zinc-900 italic tracking-tighter">Initiate <span className="text-secondary italic">Protocol</span></h3>
                                     <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none italic">Intelligence Assessment Synchronization</p>
                                </div>
                                <button onClick={onClose} className="p-4 bg-gray-50 rounded-2xl text-gray-400 hover:text-red-500 transition-colors">
                                    <XCircle className="w-6 h-6" />
                                </button>
                            </div>

                            {/* Application Selection (Only if applicationId not provided) */}
                            {!applicationId && (
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Target Candidate</label>
                                    <div className="relative group">
                                        <button 
                                            onClick={() => setIsSelectingApplication(!isSelectingApplication)}
                                            className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-left flex items-center justify-between group-hover:border-secondary/20 transition-all"
                                        >
                                            {selectedApp ? (
                                                <div className="flex items-center space-x-3">
                                                    <div className="w-8 h-8 bg-secondary/10 text-secondary rounded-xl flex items-center justify-center font-black italic text-xs">
                                                        {selectedApp.candidate.avatar_url ? <img src={selectedApp.candidate.avatar_url} className="w-full h-full object-cover rounded-xl" /> : selectedApp.candidate.full_name[0]}
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-black text-zinc-900 leading-none">{selectedApp.candidate.full_name}</p>
                                                        <p className="text-[10px] text-gray-400 font-bold italic">{selectedApp.job.title}</p>
                                                    </div>
                                                </div>
                                            ) : (
                                                <span className="text-gray-400 font-bold italic text-sm">Select Candidate Node...</span>
                                            )}
                                            <ChevronDown className={`w-4 h-4 text-gray-300 transition-transform ${isSelectingApplication ? 'rotate-180' : ''}`} />
                                        </button>

                                        {isSelectingApplication && (
                                            <motion.div 
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-100 rounded-[32px] shadow-2xl z-50 overflow-hidden"
                                            >
                                                <div className="p-4 border-b border-gray-50">
                                                    <div className="relative">
                                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                                        <input 
                                                            type="text"
                                                            placeholder="Filter candidates..."
                                                            value={searchQuery}
                                                            onChange={(e) => setSearchQuery(e.target.value)}
                                                            className="w-full pl-10 pr-4 py-2 bg-gray-50 rounded-xl text-xs font-bold outline-none"
                                                        />
                                                    </div>
                                                </div>
                                                <div className="max-h-48 overflow-y-auto p-2 space-y-1">
                                                    {filteredApplications.map(app => (
                                                        <button 
                                                            key={app.id}
                                                            onClick={() => {
                                                                setSelectedApplicationId(app.id);
                                                                setIsSelectingApplication(false);
                                                            }}
                                                            className="w-full p-3 rounded-2xl hover:bg-secondary/5 flex items-center space-x-3 transition-colors text-left"
                                                        >
                                                            <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center font-black text-[10px] italic">
                                                                {app.candidate.avatar_url ? <img src={app.candidate.avatar_url} className="w-full h-full object-cover rounded-lg" /> : app.candidate.full_name[0]}
                                                            </div>
                                                            <div>
                                                                <p className="text-[10px] font-black text-zinc-900 leading-none">{app.candidate.full_name}</p>
                                                                <p className="text-[8px] text-gray-400 font-bold italic">{app.job.title}</p>
                                                            </div>
                                                        </button>
                                                    ))}
                                                    {filteredApplications.length === 0 && (
                                                        <p className="text-[10px] text-gray-400 font-bold italic p-4 text-center">No matching nodes found.</p>
                                                    )}
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-8">
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Deployment Date</label>
                                    <div className="relative">
                                        <Calendar className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
                                        <input 
                                            type="date" 
                                            value={scheduleForm.date}
                                            onChange={(e) => setScheduleForm({...scheduleForm, date: e.target.value})}
                                            className="w-full pl-14 pr-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Sync Time</label>
                                    <div className="relative">
                                        <Clock className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" />
                                        <input 
                                            type="time" 
                                            value={scheduleForm.time}
                                            onChange={(e) => setScheduleForm({...scheduleForm, time: e.target.value})}
                                            className="w-full pl-14 pr-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Mission Type</label>
                                    <select 
                                        value={scheduleForm.type}
                                        onChange={(e) => setScheduleForm({...scheduleForm, type: e.target.value})}
                                        className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold outline-none focus:ring-4 focus:ring-secondary/5 transition-all appearance-none"
                                    >
                                        <option value="technical">Technical Assessment</option>
                                        <option value="behavioral">Behavioral Scan</option>
                                        <option value="video">Initial Video Sync</option>
                                        <option value="panel">Executive Panel</option>
                                    </select>
                                </div>
                                <div className="space-y-4">
                                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Duration</label>
                                    <select 
                                        value={scheduleForm.duration}
                                        onChange={(e) => setScheduleForm({...scheduleForm, duration: Number(e.target.value)})}
                                        className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-3xl text-sm font-bold outline-none focus:ring-4 focus:ring-secondary/5 transition-all appearance-none"
                                    >
                                        <option value={30}>30 Minutes</option>
                                        <option value={60}>60 Minutes</option>
                                        <option value={90}>90 Minutes</option>
                                        <option value={120}>120 Minutes</option>
                                    </select>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic ml-4">Candidate Instructions</label>
                                <textarea 
                                    placeholder="Enter additional intel for the candidate..."
                                    value={scheduleForm.notes}
                                    onChange={(e) => setScheduleForm({...scheduleForm, notes: e.target.value})}
                                    className="w-full px-6 py-4 bg-gray-50 border border-gray-100 rounded-[32px] text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all h-32 resize-none"
                                />
                            </div>

                            <button 
                                onClick={handleSchedule}
                                disabled={isSaving || (!applicationId && !selectedApplicationId)}
                                className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-xs uppercase tracking-[0.3em] italic hover:bg-secondary transition-all shadow-2xl flex items-center justify-center space-x-3 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isSaving ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <>
                                        <Send className="w-4 h-4" />
                                        <span>Commit Synchronization</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
