"use client";

import { useEffect, useState } from "react";
import { 
    Shield, 
    Bell, 
    CreditCard, 
    Loader2, 
    Lock, 
    Smartphone, 
    Globe, 
    Mail, 
    Zap,
    ChevronRight,
    Key,
    Activity,
    LogOut,
    Trash2,
    CheckCircle2
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import NotificationToggles from "@/components/dashboard/settings/NotificationToggles";
import ApiKeyManager from "@/components/dashboard/settings/ApiKeyManager";
import SessionManager from "@/components/dashboard/settings/SessionManager";
import { motion, AnimatePresence } from "framer-motion";

export default function Settings() {
    const supabase = createClient();
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("Security");
    const [resetSent, setResetSent] = useState(false);
    const [deleting, setDeleting] = useState(false);

    useEffect(() => {
        const timer = setTimeout(() => setLoading(false), 500);
        return () => clearTimeout(timer);
    }, []);

    const handlePasswordReset = async () => {
        const { data: { user } } = await supabase.auth.getUser();
        if (user?.email) {
            const { error } = await supabase.auth.resetPasswordForEmail(user.email, {
                redirectTo: `${window.location.origin}/dashboard/settings?reset=true`,
            });
            if (!error) {
                setResetSent(true);
                setTimeout(() => setResetSent(false), 5000);
            }
        }
    };

    const handleDeleteAccount = async () => {
        if (!confirm("Are you absolutely sure? This will terminate your operational identity permanently.")) return;
        setDeleting(true);
        // In a real HS environment, we'd call a server action or edge function to delete the user completely
        // For now, we sign out and redirect to home
        await supabase.auth.signOut();
        window.location.href = "/";
    };

    if (loading) return null;

    const tabs = [
        { icon: <Shield className="w-4 h-4" />, label: "Security" },
        { icon: <Bell className="w-4 h-4" />, label: "Notifications" },
        { icon: <Key className="w-4 h-4" />, label: "API Keys" },
        { icon: <Activity className="w-4 h-4" />, label: "Analytics" },
        { icon: <CreditCard className="w-4 h-4" />, label: "Billing & Plans" },
    ];

    return (
        <div className="max-w-6xl mx-auto space-y-12 pb-20">
            <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                <div className="space-y-4">
                    <div className="inline-flex items-center space-x-2 px-3 py-1 bg-zinc-900 text-white rounded-full">
                        <Shield className="w-3 h-3 text-primary" />
                        <span className="text-[10px] font-black uppercase tracking-widest leading-none">Global HQ Configuration</span>
                    </div>
                    <div>
                        <h1 className="text-5xl font-black font-display text-zinc-900 italic tracking-tight uppercase leading-none">Network Parameters</h1>
                        <p className="text-gray-500 font-bold uppercase tracking-widest text-xs mt-4">Manage your neural security infrastructure and operational protocols.</p>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
                {/* Sidebar Navigation */}
                <div className="space-y-2 sticky top-24 self-start">
                    {tabs.map((tab) => (
                        <button 
                            key={tab.label} 
                            onClick={() => setActiveTab(tab.label)}
                            className={`w-full flex items-center justify-between px-6 py-5 rounded-[28px] text-sm font-black transition-all group ${
                                activeTab === tab.label 
                                ? "bg-zinc-900 text-white shadow-xl shadow-zinc-900/10 scale-[1.02]" 
                                : "text-gray-400 hover:text-zinc-900 hover:bg-gray-50"
                            }`}
                        >
                            <div className="flex items-center space-x-4">
                                <span className={`transition-colors ${activeTab === tab.label ? "text-primary" : ""}`}>{tab.icon}</span>
                                <span className="uppercase tracking-[0.2em] text-[10px]">{tab.label}</span>
                            </div>
                            <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === tab.label ? "translate-x-0" : "-translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0"}`} />
                        </button>
                    ))}
                </div>

                {/* Main Settings Content */}
                <div className="lg:col-span-3 space-y-12 min-h-[600px]">
                    <AnimatePresence mode="wait">
                        {/* Security Section */}
                        {activeTab === "Security" && (
                            <motion.div 
                                key="security" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
                                className="space-y-12"
                            >
                                <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10 group relative overflow-hidden">
                                     <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-[60px] rounded-full" />
                                     <div className="flex items-center space-x-4">
                                        <div className="p-3 bg-zinc-900 rounded-2xl">
                                            <Lock className="w-5 h-5 text-primary" />
                                        </div>
                                        <h3 className="text-xl font-black text-zinc-900 italic uppercase">Access Encryption</h3>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between p-6 bg-gray-50/50 rounded-[32px] border border-gray-100/50">
                                            <div className="space-y-1">
                                                <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">Security Key (Password)</p>
                                                <p className="text-xs text-gray-400 font-bold italic">Trigger a neural reset link to your registered comms channel.</p>
                                            </div>
                                            <button 
                                                onClick={handlePasswordReset}
                                                className="px-8 py-3 bg-zinc-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic hover:scale-105 active:scale-95 transition-all shadow-xl"
                                            >
                                                Initialize Reset
                                            </button>
                                        </div>
                                        {resetSent && (
                                            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="flex items-center space-x-3 text-emerald-600 bg-emerald-50 p-4 rounded-2xl border border-emerald-100">
                                                <CheckCircle2 className="w-4 h-4" />
                                                <span className="text-[10px] font-black uppercase tracking-widest">Decryption link established. Check your inbox.</span>
                                            </motion.div>
                                        )}
                                    </div>
                                </div>

                                <SessionManager />

                                <div className="bg-red-50/50 border border-red-100 rounded-[40px] p-10 flex items-center justify-between group overflow-hidden relative">
                                     <div className="absolute right-0 top-0 w-32 h-full bg-red-600 skew-x-[15deg] translate-x-16 opacity-0 group-hover:opacity-5 transition-all duration-700" />
                                     <div className="relative z-10">
                                        <h4 className="text-xl font-black text-red-600 italic tracking-tight uppercase">Operational Deactivation</h4>
                                        <p className="text-xs text-red-400 font-bold uppercase tracking-widest mt-1">Permanent operative deletion protocol</p>
                                     </div>
                                     <button 
                                        onClick={handleDeleteAccount}
                                        className="relative z-10 px-8 py-4 bg-red-600 text-white rounded-[24px] font-black text-xs uppercase tracking-widest hover:bg-red-700 transition-all shadow-xl shadow-red-600/20 italic"
                                     >
                                         Terminate Access
                                     </button>
                                </div>
                            </motion.div>
                        )}

                        {/* Notifications Section */}
                        {activeTab === "Notifications" && (
                            <motion.div key="notifications" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                                <NotificationToggles />
                            </motion.div>
                        )}

                        {/* API Access Section */}
                        {activeTab === "API Keys" && (
                            <motion.div key="api" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                                <ApiKeyManager />
                            </motion.div>
                        )}

                        {/* Analytics Placeholder Link */}
                        {activeTab === "Analytics" && (
                             <motion.div key="analytics" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                                 <div className="bg-zinc-900 border border-zinc-800 rounded-[40px] p-12 text-white relative overflow-hidden text-center space-y-8">
                                     <div className="relative z-10">
                                        <Activity className="w-16 h-16 text-primary mx-auto mb-6" />
                                        <h3 className="text-3xl font-black font-display italic tracking-tight mb-4 uppercase">Advanced Analytics Dashboard</h3>
                                        <p className="text-gray-400 font-bold uppercase tracking-widest text-xs max-w-md mx-auto mb-10 leading-relaxed">
                                            Track your recruitment signal, identity pings, and match efficiency across the global grid.
                                        </p>
                                        <a href="/dashboard/analytics" className="inline-block px-12 py-5 bg-primary text-white rounded-[32px] font-black text-xs uppercase tracking-widest italic shadow-2xl hover:scale-105 active:scale-95 transition-all">
                                            Initialize Analytics Sync
                                        </a>
                                     </div>
                                     <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_50%_0%,rgba(0,102,255,0.05),transparent)] pointer-events-none" />
                                 </div>
                             </motion.div>
                        )}

                        {/* Billing Section */}
                        {activeTab === "Billing & Plans" && (
                             <motion.div key="billing" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="space-y-8">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-[40px] p-12 text-white relative overflow-hidden group">
                                     <div className="relative z-10 space-y-8 text-center md:text-left">
                                        <div className="flex flex-col md:flex-row items-center md:items-end justify-between gap-6">
                                            <div className="space-y-2">
                                                <h3 className="text-5xl font-black font-display italic tracking-tighter uppercase leading-none">HireSight <span className="text-primary italic">Elite</span></h3>
                                                <p className="text-primary font-black uppercase tracking-[0.4em] text-[10px]">Active Protocol: Neural Tier 1</p>
                                            </div>
                                            <div className="p-6 bg-white/5 rounded-[32px] border border-white/10 text-primary group-hover:scale-110 transition-all duration-500">
                                                <Zap className="w-10 h-10" />
                                            </div>
                                        </div>
                                        <div className="p-10 bg-white/5 rounded-[40px] border border-white/5 backdrop-blur-2xl">
                                            <p className="text-lg text-gray-300 font-medium leading-relaxed mb-8 italic">
                                                Neural pattern matching, unlimited operative slots, and deep intelligence exports.
                                            </p>
                                            <button className="w-full py-6 bg-white text-zinc-900 rounded-[28px] font-black text-sm uppercase tracking-widest italic shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all">Synchronize Credits</button>
                                        </div>
                                     </div>
                                     <div className="absolute bottom-[-20%] left-[-10%] w-[60%] h-[60%] bg-primary/10 blur-[100px] rounded-full pointer-events-none" />
                                 </div>
                             </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}
