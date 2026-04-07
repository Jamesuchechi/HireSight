"use client";

import { useEffect, useState, useCallback } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Bell, Check, CheckCheck, Trash2, Trash, 
    ExternalLink, Briefcase, MessageCircle, Zap, 
    ShieldCheck, Calendar, User, Star, BrainCircuit,
    AlertCircle, ChevronLeft, ChevronRight, Filter
} from "lucide-react";
import { motion } from "framer-motion";
import Link from "next/link";
import { formatDistanceToNow, format } from "date-fns";

interface Notification {
    id: string;
    title: string;
    message: string;
    type: string;
    action_url: string | null;
    action_text: string | null;
    is_read: boolean;
    created_at: string;
}

const TYPE_CONFIG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
    application_received:       { icon: <Briefcase className="w-5 h-5" />,     label: "Applications",  color: "bg-blue-500" },
    application_status_changed: { icon: <Briefcase className="w-5 h-5" />,     label: "Applications",  color: "bg-indigo-500" },
    new_message:                { icon: <MessageCircle className="w-5 h-5" />, label: "Messages",      color: "bg-emerald-500" },
    new_follower:               { icon: <User className="w-5 h-5" />,          label: "Social",        color: "bg-violet-500" },
    new_job_from_follow:        { icon: <Zap className="w-5 h-5" />,           label: "Jobs",          color: "bg-yellow-500" },
    interview_scheduled:        { icon: <Calendar className="w-5 h-5" />,      label: "Interviews",    color: "bg-cyan-500" },
    screening_completed:        { icon: <ShieldCheck className="w-5 h-5" />,   label: "Screening",     color: "bg-teal-500" },
    job_expiring:               { icon: <AlertCircle className="w-5 h-5" />,   label: "Jobs",          color: "bg-orange-500" },
    profile_viewed:             { icon: <User className="w-5 h-5" />,          label: "Social",        color: "bg-pink-500" },
    assessment_passed:          { icon: <BrainCircuit className="w-5 h-5" />,  label: "Assessments",   color: "bg-primary" },
    system:                     { icon: <Star className="w-5 h-5" />,          label: "System",        color: "bg-gray-500" },
};

const FILTER_OPTIONS = [
    { key: "all",                       label: "All",          types: null },
    { key: "unread",                    label: "Unread",       types: null },
    { key: "applications",              label: "Applications", types: ["application_received","application_status_changed"] },
    { key: "messages",                  label: "Messages",     types: ["new_message"] },
    { key: "jobs",                      label: "Jobs",         types: ["new_job_from_follow","job_expiring"] },
    { key: "assessments",               label: "Assessments",  types: ["assessment_passed"] },
    { key: "system",                    label: "System",       types: ["system","new_follower","profile_viewed","interview_scheduled","screening_completed"] },
];

const PAGE_SIZE = 12;

export default function NotificationsPage() {
    const supabase = createClient();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [totalCount, setTotalCount] = useState(0);
    const [unreadCount, setUnreadCount] = useState(0);
    const [activeFilter, setActiveFilter] = useState("all");
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [userId, setUserId] = useState<string | null>(null);

    const fetchNotifications = useCallback(async (uid: string, filter: string, pg: number) => {
        setLoading(true);
        let query = supabase
            .from("notifications")
            .select("*", { count: "exact" })
            .eq("user_id", uid)
            .order("created_at", { ascending: false })
            .range((pg - 1) * PAGE_SIZE, pg * PAGE_SIZE - 1);

        const filterOption = FILTER_OPTIONS.find(f => f.key === filter);
        if (filter === "unread") {
            query = query.eq("is_read", false);
        } else if (filterOption?.types) {
            query = query.in("type", filterOption.types);
        }

        const { data, count } = await query;
        if (data) setNotifications(data);
        if (count !== null) setTotalCount(count);
        setLoading(false);
    }, [supabase]);

    useEffect(() => {
        const init = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;
            setUserId(user.id);

            // Get unread count separately (always global, not filtered)
            const { count } = await supabase
                .from("notifications")
                .select("*", { count: "exact", head: true })
                .eq("user_id", user.id)
                .eq("is_read", false);
            if (count !== null) setUnreadCount(count);

            fetchNotifications(user.id, "all", 1);
        };
        init();
    }, [supabase, fetchNotifications]);

    useEffect(() => {
        if (userId) fetchNotifications(userId, activeFilter, page);
    }, [activeFilter, page, userId, fetchNotifications]);

    const handleFilterChange = (key: string) => {
        setActiveFilter(key);
        setPage(1);
    };

    const markAsRead = async (id: string, currentRead: boolean) => {
        if (currentRead) return;
        await supabase.from("notifications").update({ is_read: true }).eq("id", id);
        setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
        setUnreadCount(prev => Math.max(0, prev - 1));
    };

    const toggleRead = async (n: Notification) => {
        const newState = !n.is_read;
        await supabase.from("notifications").update({ is_read: newState }).eq("id", n.id);
        setNotifications(prev => prev.map(x => x.id === n.id ? { ...x, is_read: newState } : x));
        setUnreadCount(prev => newState ? Math.max(0, prev - 1) : prev + 1);
    };

    const deleteOne = async (id: string, wasUnread: boolean) => {
        await supabase.from("notifications").delete().eq("id", id);
        setNotifications(prev => prev.filter(x => x.id !== id));
        setTotalCount(prev => prev - 1);
        if (wasUnread) setUnreadCount(prev => Math.max(0, prev - 1));
    };

    const markAllRead = async () => {
        if (!userId) return;
        await supabase.from("notifications").update({ is_read: true }).eq("user_id", userId).eq("is_read", false);
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
    };

    const deleteAll = async () => {
        if (!userId) return;
        if (!confirm("Delete all notifications? This cannot be undone.")) return;
        await supabase.from("notifications").delete().eq("user_id", userId);
        setNotifications([]);
        setTotalCount(0);
        setUnreadCount(0);
    };

    const totalPages = Math.ceil(totalCount / PAGE_SIZE);

    return (
        <div className="max-w-5xl mx-auto space-y-10 pb-32">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div className="space-y-3">
                    <div className="flex items-center space-x-3 text-primary">
                        <Bell className="w-6 h-6" />
                        <span className="text-[10px] font-black uppercase tracking-[0.2em] italic">Activity Feed</span>
                    </div>
                    <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter uppercase leading-none">
                        Notification <span className="text-primary">Centre</span>
                    </h1>
                    <p className="text-gray-500 font-bold">
                        {unreadCount > 0 ? (
                            <span><span className="text-primary font-black">{unreadCount} unread</span> · {totalCount} total notifications</span>
                        ) : (
                            <span>{totalCount} notifications</span>
                        )}
                    </p>
                </div>

                {/* Bulk Actions */}
                <div className="flex items-center gap-3">
                    {unreadCount > 0 && (
                        <button
                            onClick={markAllRead}
                            className="flex items-center space-x-2 px-6 py-3 bg-white border border-gray-100 rounded-2xl text-[10px] font-black uppercase tracking-widest italic hover:bg-primary hover:text-white hover:border-primary transition-all shadow-sm"
                        >
                            <CheckCheck className="w-4 h-4" />
                            <span>Mark All Read</span>
                        </button>
                    )}
                    {notifications.length > 0 && (
                        <button
                            onClick={deleteAll}
                            className="flex items-center space-x-2 px-6 py-3 bg-white border border-gray-100 rounded-2xl text-[10px] font-black uppercase tracking-widest italic hover:bg-red-500 hover:text-white hover:border-red-500 transition-all shadow-sm"
                        >
                            <Trash className="w-4 h-4" />
                            <span>Delete All</span>
                        </button>
                    )}
                </div>
            </header>

            {/* Filter Tabs */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
                {FILTER_OPTIONS.map(f => (
                    <button
                        key={f.key}
                        onClick={() => handleFilterChange(f.key)}
                        className={`px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest italic whitespace-nowrap transition-all ${
                            activeFilter === f.key
                            ? "bg-zinc-900 text-white shadow-lg"
                            : "bg-white text-gray-400 border border-gray-100 hover:border-zinc-300 hover:text-zinc-700"
                        }`}
                    >
                        {f.label}
                        {f.key === "unread" && unreadCount > 0 && (
                            <span className="ml-2 px-1.5 py-0.5 bg-primary text-white text-[8px] rounded-full">{unreadCount}</span>
                        )}
                    </button>
                ))}
            </div>

            {/* Notifications List */}
            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : notifications.length === 0 ? (
                <div className="bg-white border-2 border-dashed border-gray-100 rounded-[56px] p-24 text-center space-y-6">
                    <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto text-gray-200">
                        <Bell className="w-10 h-10" />
                    </div>
                    <div className="space-y-3">
                        <h3 className="text-2xl font-black text-zinc-900 italic tracking-tight uppercase">All Clear</h3>
                        <p className="text-gray-400 font-bold italic max-w-sm mx-auto">
                            {activeFilter === "unread" ? "No unread notifications — you're all caught up!" : "No notifications in this category."}
                        </p>
                    </div>
                    {activeFilter !== "all" && (
                        <button
                            onClick={() => handleFilterChange("all")}
                            className="inline-flex px-8 py-3 bg-zinc-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest italic hover:bg-primary transition-all"
                        >
                            View All
                        </button>
                    )}
                </div>
            ) : (
                <div className="bg-white rounded-[48px] border border-gray-100 shadow-sm overflow-hidden divide-y divide-gray-50">
                    {notifications.map((n, idx) => {
                        const config = TYPE_CONFIG[n.type] || TYPE_CONFIG.system;
                        const NotifWrapper = n.action_url ? Link : "div" as any;
                        return (
                            <motion.div
                                key={n.id}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: idx * 0.03 }}
                                className={`group flex items-start gap-6 px-8 py-6 transition-all ${!n.is_read ? "bg-primary/[0.02]" : "hover:bg-gray-50/60"}`}
                            >
                                {/* Type Icon */}
                                <div className={`w-12 h-12 min-w-[48px] rounded-[20px] ${config.color} text-white flex items-center justify-center shadow-sm mt-0.5`}>
                                    {config.icon}
                                </div>

                                {/* Content */}
                                <NotifWrapper
                                    href={n.action_url || "#"}
                                    onClick={() => markAsRead(n.id, n.is_read)}
                                    className="flex-1 min-w-0"
                                >
                                    <div className="flex items-start justify-between gap-4">
                                        <p className={`font-black text-base leading-tight ${!n.is_read ? "text-zinc-900" : "text-zinc-600"}`}>
                                            {n.title}
                                        </p>
                                        <div className="flex items-center gap-2 shrink-0">
                                            {!n.is_read && <span className="w-2.5 h-2.5 bg-primary rounded-full" />}
                                            <span className="text-[9px] font-black text-gray-300 uppercase tracking-widest whitespace-nowrap">
                                                {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                                            </span>
                                        </div>
                                    </div>
                                    <p className="text-sm font-bold text-gray-400 mt-1 italic">{n.message}</p>
                                    {n.action_url && n.action_text && (
                                        <span className="inline-flex items-center gap-1 mt-3 text-[10px] font-black text-primary uppercase tracking-widest italic">
                                            {n.action_text} <ExternalLink className="w-3 h-3" />
                                        </span>
                                    )}
                                </NotifWrapper>

                                {/* Per-item Actions */}
                                <div className="flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                                    <button
                                        onClick={() => toggleRead(n)}
                                        title={n.is_read ? "Mark as unread" : "Mark as read"}
                                        className="p-2 text-gray-300 hover:text-primary hover:bg-primary/5 rounded-xl transition-all"
                                    >
                                        <Check className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => deleteOne(n.id, !n.is_read)}
                                        title="Delete notification"
                                        className="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="p-3 bg-white border border-gray-100 rounded-2xl hover:bg-zinc-900 hover:text-white hover:border-zinc-900 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">
                        Page {page} of {totalPages}
                    </span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="p-3 bg-white border border-gray-100 rounded-2xl hover:bg-zinc-900 hover:text-white hover:border-zinc-900 transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-sm"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
            )}
        </div>
    );
}
