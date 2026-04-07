"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Bell, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

interface NotificationPrefs {
    frequency: 'instant' | 'daily' | 'weekly' | 'off';
    notify_jobs: boolean;
    notify_applications: boolean;
    notify_messages: boolean;
    notify_views: boolean;
}

export default function NotificationToggles() {
    const supabase = createClient();
    const [prefs, setPrefs] = useState<NotificationPrefs | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState<string | null>(null);

    useEffect(() => {
        const fetchPrefs = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                const { data } = await supabase
                    .from("notification_preferences")
                    .select("*")
                    .eq("user_id", user.id)
                    .single();
                
                if (data) {
                    setPrefs(data as any);
                }
            }
            setLoading(false);
        };
        fetchPrefs();
    }, [supabase]);

    const togglePref = async (key: keyof NotificationPrefs) => {
        if (!prefs) return;
        setSaving(key);
        
        const newPrefs = { ...prefs, [key]: !prefs[key] };
        setPrefs(newPrefs);

        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            await supabase
                .from("notification_preferences")
                .update({ [key]: newPrefs[key] })
                .eq("user_id", user.id);
        }
        setSaving(null);
    };

    const updateFrequency = async (freq: NotificationPrefs['frequency']) => {
        if (!prefs) return;
        setSaving('frequency');
        
        const newPrefs = { ...prefs, frequency: freq };
        setPrefs(newPrefs);

        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            await supabase
                .from("notification_preferences")
                .update({ frequency: freq })
                .eq("user_id", user.id);
        }
        setSaving(null);
    };

    if (loading) return <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;
    if (!prefs) return null;

    const sections = [
        { key: 'notify_jobs', label: 'Job Matches', desc: 'New opportunities matching your neural profile' },
        { key: 'notify_applications', label: 'Application Updates', desc: 'Real-time status changes and interview requests' },
        { key: 'notify_messages', label: 'Direct Transmissions', desc: 'Secure messages from recruiters and candidates' },
        { key: 'notify_views', label: 'Identity Pings', desc: 'Alerts when your profile is viewed by authorized entities' },
    ];

    return (
        <div className="bg-white border border-gray-100 rounded-[40px] p-8 md:p-10 shadow-sm space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <div className="p-3 bg-zinc-900 rounded-2xl text-primary">
                        <Bell className="w-5 h-5" />
                    </div>
                    <h3 className="text-xl font-black text-zinc-900 italic uppercase tracking-tight">Signal Parameters</h3>
                </div>
                <div className="hidden md:block">
                    <select 
                        value={prefs.frequency}
                        onChange={(e) => updateFrequency(e.target.value as any)}
                        className="bg-gray-50 border-2 border-transparent focus:border-primary/20 p-3 rounded-xl text-[10px] font-black uppercase tracking-widest outline-none transition-all"
                    >
                        <option value="instant">Instant Sync</option>
                        <option value="daily">Daily Digest</option>
                        <option value="weekly">Weekly Rollup</option>
                        <option value="off">Muted</option>
                    </select>
                </div>
            </div>

            <div className="space-y-4">
                {sections.map((section) => (
                    <div 
                        key={section.key} 
                        className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px] hover:bg-gray-50/50 transition-all group"
                    >
                        <div className="space-y-1">
                            <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">{section.label}</p>
                            <p className="text-xs text-gray-400 font-bold max-w-xs">{section.desc}</p>
                        </div>
                        <button 
                            onClick={() => togglePref(section.key as any)}
                            disabled={saving === section.key}
                            className={`w-14 h-7 rounded-full relative transition-all duration-300 ${prefs[section.key as keyof NotificationPrefs] ? 'bg-primary' : 'bg-gray-200'}`}
                        >
                            <motion.div 
                                animate={{ x: prefs[section.key as keyof NotificationPrefs] ? 30 : 4 }}
                                className="absolute top-1 w-5 h-5 bg-white rounded-full shadow-lg"
                            />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}
