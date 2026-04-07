"use client";

import { useEffect, useState, useRef } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Bell, X, Check, CheckCheck, Trash2, Trash, 
    ArrowRight, Briefcase, MessageCircle, Zap,
    ShieldCheck, Calendar, User, Star, Settings,
    BrainCircuit, ExternalLink, AlertCircle
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

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

const TYPE_CONFIG: Record<string, { icon: React.ReactNode; color: string }> = {
    application_received:      { icon: <Briefcase className="w-4 h-4" />,     color: "bg-blue-500" },
    application_status_changed:{ icon: <Briefcase className="w-4 h-4" />,     color: "bg-indigo-500" },
    new_message:               { icon: <MessageCircle className="w-4 h-4" />, color: "bg-emerald-500" },
    new_follower:              { icon: <User className="w-4 h-4" />,          color: "bg-violet-500" },
    new_job_from_follow:       { icon: <Zap className="w-4 h-4" />,           color: "bg-yellow-500" },
    interview_scheduled:       { icon: <Calendar className="w-4 h-4" />,      color: "bg-cyan-500" },
    screening_completed:       { icon: <ShieldCheck className="w-4 h-4" />,   color: "bg-teal-500" },
    job_expiring:              { icon: <AlertCircle className="w-4 h-4" />,   color: "bg-orange-500" },
    profile_viewed:            { icon: <User className="w-4 h-4" />,          color: "bg-pink-500" },
    assessment_passed:         { icon: <BrainCircuit className="w-4 h-4" />,  color: "bg-primary" },
    system:                    { icon: <Star className="w-4 h-4" />,          color: "bg-gray-500" },
};

export default function NotificationBell({ userId }: { userId: string }) {
    const supabase = createClient();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const drawerRef = useRef<HTMLDivElement>(null);

    // Initial fetch
    const fetchNotifications = async () => {
        const { data } = await supabase
            .from("notifications")
            .select("*")
            .eq("user_id", userId)
            .order("created_at", { ascending: false })
            .limit(15);

        if (data) {
            setNotifications(data);
            setUnreadCount(data.filter(n => !n.is_read).length);
        }
    };

    useEffect(() => {
        fetchNotifications();

        // Supabase Realtime subscription for live updates
        const channel = supabase
            .channel(`notifications:${userId}`)
            .on(
                "postgres_changes",
                { 
                    event: "*", 
                    schema: "public", 
                    table: "notifications",
                    filter: `user_id=eq.${userId}`
                },
                () => {
                    // Re-fetch on any change (insert, update, delete)
                    fetchNotifications();
                }
            )
            .subscribe();

        return () => { supabase.removeChannel(channel); };
    }, [userId]);

    // Close drawer on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
                setDrawerOpen(false);
            }
        };
        if (drawerOpen) document.addEventListener("mousedown", handler);
        return () => document.removeEventListener("mousedown", handler);
    }, [drawerOpen]);

    const markAsRead = async (id: string) => {
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

    const deleteOne = async (id: string) => {
        const n = notifications.find(x => x.id === id);
        await supabase.from("notifications").delete().eq("id", id);
        setNotifications(prev => prev.filter(x => x.id !== id));
        if (n && !n.is_read) setUnreadCount(prev => Math.max(0, prev - 1));
    };

    const markAllRead = async () => {
        await supabase.from("notifications").update({ is_read: true }).eq("user_id", userId).eq("is_read", false);
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
    };

    const deleteAll = async () => {
        if (!confirm("Delete all notifications? This cannot be undone.")) return;
        await supabase.from("notifications").delete().eq("user_id", userId);
        setNotifications([]);
        setUnreadCount(0);
    };

    const handleItemClick = (n: Notification) => {
        if (!n.is_read) markAsRead(n.id);
        setDrawerOpen(false);
    };

    // Group by date
    const today = new Date(); today.setHours(0,0,0,0);
    const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1);
    const groups: { label: string; items: Notification[] }[] = [
        { label: "Today",     items: notifications.filter(n => new Date(n.created_at) >= today) },
        { label: "Yesterday", items: notifications.filter(n => { const d = new Date(n.created_at); return d >= yesterday && d < today; }) },
        { label: "Earlier",   items: notifications.filter(n => new Date(n.created_at) < yesterday) },
    ].filter(g => g.items.length > 0);

    return (
        <div className="relative" ref={drawerRef}>
            {/* Bell Button */}
            <button
                onClick={() => setDrawerOpen(o => !o)}
                className="relative p-2.5 bg-white border border-gray-100 rounded-2xl hover:bg-gray-50 transition-all shadow-sm"
                aria-label={`${unreadCount} unread notifications`}
            >
                <Bell className="w-5 h-5 text-gray-500" />
                <AnimatePresence>
                    {unreadCount > 0 && (
                        <motion.span
                            key="badge"
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0 }}
                            className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 px-1.5 bg-primary text-white text-[9px] font-black rounded-full flex items-center justify-center border-2 border-white shadow-lg"
                        >
                            {unreadCount > 99 ? "99+" : unreadCount}
                        </motion.span>
                    )}
                </AnimatePresence>
            </button>

            {/* Slide-out Drawer */}
            <AnimatePresence>
                {drawerOpen && (
                    <motion.div
                        key="drawer"
                        initial={{ opacity: 0, y: -10, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -10, scale: 0.97 }}
                        transition={{ duration: 0.18, ease: "easeOut" }}
                        className="absolute right-0 top-14 w-[420px] max-h-[600px] bg-white rounded-[40px] shadow-2xl border border-gray-100 flex flex-col z-50 overflow-hidden"
                    >
                        {/* Drawer Header */}
                        <div className="flex items-center justify-between px-8 pt-8 pb-4 border-b border-gray-50 shrink-0">
                            <div>
                                <h3 className="text-xl font-black text-zinc-900 italic tracking-tight">Notifications</h3>
                                <p className="text-[9px] font-black text-gray-400 uppercase tracking-[0.2em] mt-0.5">
                                    {unreadCount} Unread
                                </p>
                            </div>
                            <div className="flex items-center space-x-2">
                                {unreadCount > 0 && (
                                    <button
                                        onClick={markAllRead}
                                        title="Mark all as read"
                                        className="p-2 text-gray-400 hover:text-primary hover:bg-primary/5 rounded-xl transition-all"
                                    >
                                        <CheckCheck className="w-4 h-4" />
                                    </button>
                                )}
                                {notifications.length > 0 && (
                                    <button
                                        onClick={deleteAll}
                                        title="Delete all"
                                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
                                    >
                                        <Trash className="w-4 h-4" />
                                    </button>
                                )}
                                <button
                                    onClick={() => setDrawerOpen(false)}
                                    className="p-2 text-gray-400 hover:text-zinc-900 hover:bg-gray-50 rounded-xl transition-all"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        {/* Notification List */}
                        <div className="flex-1 overflow-y-auto scrollbar-hide">
                            {notifications.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-20 space-y-4 text-center">
                                    <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center text-gray-300">
                                        <Bell className="w-8 h-8" />
                                    </div>
                                    <div>
                                        <p className="font-black italic text-zinc-900 text-sm">All Caught Up</p>
                                        <p className="text-[10px] font-bold text-gray-400 mt-1">No notifications yet.</p>
                                    </div>
                                </div>
                            ) : (
                                <div className="py-4">
                                    {groups.map(group => (
                                        <div key={group.label}>
                                            <p className="px-8 py-3 text-[8px] font-black text-gray-300 uppercase tracking-[0.3em]">{group.label}</p>
                                            {group.items.map(n => {
                                                const config = TYPE_CONFIG[n.type] || TYPE_CONFIG.system;
                                                const NotifWrapper = n.action_url ? Link : "div" as any;

                                                return (
                                                    <div
                                                        key={n.id}
                                                        className={`group flex items-start gap-4 px-8 py-4 transition-all ${!n.is_read ? "bg-primary/3" : "hover:bg-gray-50/80"}`}
                                                    >
                                                        {/* Type Icon */}
                                                        <div className={`w-9 h-9 min-w-[36px] rounded-[14px] ${config.color} text-white flex items-center justify-center shadow-sm mt-0.5`}>
                                                            {config.icon}
                                                        </div>

                                                        {/* Content */}
                                                        <NotifWrapper
                                                            href={n.action_url || "#"}
                                                            onClick={() => handleItemClick(n)}
                                                            className="flex-1 min-w-0"
                                                        >
                                                            <div className="flex items-start justify-between gap-2">
                                                                <p className={`text-sm font-black leading-tight ${!n.is_read ? "text-zinc-900" : "text-zinc-600"}`}>
                                                                    {n.title}
                                                                </p>
                                                                {!n.is_read && (
                                                                    <span className="w-2 h-2 min-w-[8px] bg-primary rounded-full mt-1" />
                                                                )}
                                                            </div>
                                                            <p className="text-[11px] font-bold text-gray-400 mt-1 line-clamp-2 italic">{n.message}</p>
                                                            <p className="text-[9px] font-black text-gray-300 uppercase tracking-widest mt-1.5">
                                                                {formatDistanceToNow(new Date(n.created_at), { addSuffix: true })}
                                                            </p>
                                                        </NotifWrapper>

                                                        {/* Per-item Actions (visible on hover) */}
                                                        <div className="flex flex-col items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                            <button
                                                                onClick={() => toggleRead(n)}
                                                                title={n.is_read ? "Mark unread" : "Mark read"}
                                                                className="p-1.5 text-gray-300 hover:text-primary hover:bg-primary/5 rounded-lg transition-all"
                                                            >
                                                                <Check className="w-3 h-3" />
                                                            </button>
                                                            <button
                                                                onClick={() => deleteOne(n.id)}
                                                                title="Delete"
                                                                className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                                            >
                                                                <Trash2 className="w-3 h-3" />
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Drawer Footer */}
                        <div className="px-8 py-6 border-t border-gray-50 shrink-0">
                            <Link
                                href="/dashboard/notifications"
                                onClick={() => setDrawerOpen(false)}
                                className="w-full flex items-center justify-center space-x-2 py-3.5 bg-zinc-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest italic hover:bg-primary transition-all"
                            >
                                <span>View All Notifications</span>
                                <ArrowRight className="w-4 h-4" />
                            </Link>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
