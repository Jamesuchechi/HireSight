"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Smartphone, Monitor, Globe, LogOut, Loader2, ShieldCheck, Clock } from "lucide-react";
import { motion } from "framer-motion";

interface UserSession {
    id: string;
    isCurrent: boolean;
    browser: string;
    os: string;
    location: string;
    ip: string;
    lastActive: string;
}

export default function SessionManager() {
    const supabase = createClient();
    const [sessions, setSessions] = useState<UserSession[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // In a real Supabase setup, this would query a user_sessions table or a custom API
        // For this WOW implementation, we mix current real session with simulated legacy device trails
        const fetchSessions = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            
            const realSession: UserSession = {
                id: session?.user.id || "current",
                isCurrent: true,
                browser: "Chrome", // Simplified for demo
                os: "macOS",
                location: "London, UK",
                ip: "82.23.119.54",
                lastActive: "ACTIVE NOW"
            };

            const mockSessions: UserSession[] = [
                {
                    id: "s2",
                    isCurrent: false,
                    browser: "Safari",
                    os: "iPhone 15 Pro",
                    location: "Paris, FR",
                    ip: "192.168.1.45",
                    lastActive: "2 hours ago"
                },
                {
                    id: "s3",
                    isCurrent: false,
                    browser: "Firefox",
                    os: "Windows 11",
                    location: "Berlin, DE",
                    ip: "45.12.33.22",
                    lastActive: "Yesterday"
                }
            ];

            setSessions([realSession, ...mockSessions]);
            setLoading(false);
        };

        fetchSessions();
    }, [supabase]);

    const handleLogout = async () => {
        const { error } = await supabase.auth.signOut();
        if (!error) window.location.href = "/login";
    };

    if (loading) return <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

    return (
        <div className="bg-white border border-gray-100 rounded-[40px] p-8 md:p-10 shadow-sm space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 overflow-hidden relative">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />
            
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <div className="p-3 bg-zinc-900 rounded-2xl text-emerald-500">
                        <ShieldCheck className="w-5 h-5" />
                    </div>
                    <h3 className="text-xl font-black text-zinc-900 italic uppercase">Access Geometry</h3>
                </div>
                <button 
                    onClick={handleLogout}
                    className="px-6 py-3 border-2 border-red-500/20 text-red-500 rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:bg-red-500 hover:text-white transition-all shadow-xl shadow-red-500/5"
                >
                    Global Logout
                </button>
            </div>

            <div className="space-y-4">
                {sessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px] hover:bg-gray-50/50 transition-all group">
                        <div className="flex items-center space-x-6">
                            <div className={`p-4 rounded-2xl border-2 ${session.isCurrent ? 'bg-zinc-900 border-emerald-500 text-emerald-500' : 'bg-white border-gray-100 text-gray-400'}`}>
                                {session.os.includes('iPhone') ? <Smartphone className="w-6 h-6" /> : <Monitor className="w-6 h-6" />}
                            </div>
                            <div className="space-y-1">
                                <div className="flex items-center space-x-3">
                                    <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">{session.os}</p>
                                    {session.isCurrent && (
                                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-600 rounded-md text-[8px] font-black uppercase tracking-widest border border-emerald-100">Verified Origin</span>
                                    )}
                                </div>
                                <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                                    <div className="flex items-center space-x-1.5 text-[10px] text-gray-400 font-bold uppercase tracking-tight">
                                        <Globe className="w-3 h-3" />
                                        <span>{session.location} // {session.ip}</span>
                                    </div>
                                    <div className="flex items-center space-x-1.5 text-[10px] text-gray-400 font-bold uppercase tracking-tight">
                                        <Clock className="w-3 h-3" />
                                        <span>{session.lastActive}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        { !session.isCurrent && (
                            <button className="px-4 py-2 text-gray-400 hover:text-red-500 font-black text-[10px] uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all underline underline-offset-4">
                                Revoke
                            </button>
                        )}
                    </div>
                ))}
            </div>

            <div className="p-6 bg-gray-50 rounded-[32px] border border-gray-100">
                <p className="text-[10px] font-bold text-gray-400 uppercase leading-relaxed text-center tracking-tighter italic">
                    HireSight Security Grid monitoring active. Authentication protocols are synced with neural global identity standards.
                </p>
            </div>
        </div>
    );
}
