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
    ChevronRight
} from "lucide-react";
import { createClient } from "@/lib/supabase/client";

export default function Settings() {
    const supabase = createClient();
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("Security");

    useEffect(() => {
        // Just a simulation for now as we don't have complex settings yet
        const timer = setTimeout(() => setLoading(false), 500);
        return () => clearTimeout(timer);
    }, []);

    if (loading) return null;

    const tabs = [
        { icon: <Shield className="w-4 h-4" />, label: "Security" },
        { icon: <Bell className="w-4 h-4" />, label: "Notifications" },
        { icon: <CreditCard className="w-4 h-4" />, label: "Billing & Plans" },
        { icon: <Globe className="w-4 h-4" />, label: "Preferences" },
    ];

    return (
        <div className="max-w-5xl mx-auto space-y-12 pb-20">
            <header>
                <div className="inline-flex items-center space-x-2 px-3 py-1 bg-zinc-900 text-white rounded-full mb-4">
                    <Shield className="w-3 h-3 text-primary" />
                    <span className="text-[10px] font-black uppercase tracking-widest">Protocol Configuration</span>
                </div>
                <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight uppercase leading-none">Global Parameters</h1>
                <p className="text-gray-500 font-bold uppercase tracking-widest text-xs mt-3">Manage your secure infrastructure and operational preferences.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
                {/* Sidebar Navigation */}
                <div className="space-y-3">
                    {tabs.map((tab) => (
                        <button 
                            key={tab.label} 
                            onClick={() => setActiveTab(tab.label)}
                            className={`w-full flex items-center justify-between px-6 py-4 rounded-[24px] text-sm font-black transition-all group ${
                                activeTab === tab.label 
                                ? "bg-zinc-900 text-white shadow-xl shadow-zinc-900/10" 
                                : "text-gray-400 hover:text-zinc-900 hover:bg-gray-50"
                            }`}
                        >
                            <div className="flex items-center space-x-3">
                                {tab.icon}
                                <span className="uppercase tracking-widest text-[11px]">{tab.label}</span>
                            </div>
                            <ChevronRight className={`w-4 h-4 transition-transform ${activeTab === tab.label ? "translate-x-0" : "-translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0"}`} />
                        </button>
                    ))}
                </div>

                {/* Main Settings Content */}
                <div className="lg:col-span-3 space-y-8">
                    {/* Security Section */}
                    {activeTab === "Security" && (
                        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                            <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        <div className="p-3 bg-zinc-900 rounded-2xl">
                                            <Lock className="w-5 h-5 text-primary" />
                                        </div>
                                        <h3 className="text-xl font-black text-zinc-900 italic uppercase">Access Protocols</h3>
                                    </div>
                                    <span className="px-3 py-1 bg-emerald-50 text-emerald-600 rounded-full text-[10px] font-black uppercase tracking-widest border border-emerald-100">Active</span>
                                </div>

                                <div className="space-y-6">
                                    <div className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px] hover:bg-gray-50 transition-all cursor-pointer group">
                                        <div className="flex items-center space-x-4">
                                            <Mail className="w-5 h-5 text-gray-400" />
                                            <div>
                                                <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">Update Security Key</p>
                                                <p className="text-xs text-gray-400 font-bold">Standard password management flow</p>
                                            </div>
                                        </div>
                                        <button className="px-5 py-2.5 bg-white border border-gray-100 rounded-xl text-[10px] font-black uppercase tracking-widest text-gray-500 group-hover:bg-zinc-900 group-hover:text-white transition-all shadow-sm">Initialize</button>
                                    </div>

                                    <div className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px] hover:bg-gray-50 transition-all cursor-pointer group">
                                        <div className="flex items-center space-x-4">
                                            <Smartphone className="w-5 h-5 text-gray-400" />
                                            <div>
                                                <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">Two-Factor Auth</p>
                                                <p className="text-xs text-gray-400 font-bold">Additional layer of biometric / device verification</p>
                                            </div>
                                        </div>
                                        <div className="w-12 h-6 bg-gray-200 rounded-full relative">
                                            <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div className="bg-red-50/50 border border-red-100 rounded-[40px] p-10 flex items-center justify-between">
                                 <div>
                                    <h4 className="text-xl font-black text-red-600 italic tracking-tight uppercase">Danger Zone</h4>
                                    <p className="text-xs text-red-400 font-bold uppercase tracking-widest mt-1">Permanent operative deactivation</p>
                                 </div>
                                 <button className="px-8 py-4 bg-red-600 text-white rounded-[24px] font-black text-xs uppercase tracking-widest hover:bg-red-700 transition-all shadow-xl shadow-red-600/20 italic">Terminate Access</button>
                            </div>
                        </div>
                    )}

                    {/* Notifications Section */}
                    {activeTab === "Notifications" && (
                        <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                             <div className="flex items-center space-x-4">
                                <div className="p-3 bg-zinc-900 rounded-2xl text-secondary">
                                    <Bell className="w-5 h-5" />
                                </div>
                                <h3 className="text-xl font-black text-zinc-900 italic uppercase">Signal Alerts</h3>
                            </div>
                            <div className="space-y-6">
                                {['Job Matches', 'Application Updates', 'Recruiter Messages', 'Marketing / Growth'].map((item) => (
                                    <div key={item} className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px]">
                                        <div>
                                            <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">{item}</p>
                                            <p className="text-xs text-gray-400 font-bold">Standard email and push notification signals</p>
                                        </div>
                                        <div className="w-12 h-6 bg-primary rounded-full relative">
                                            <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow-sm" />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Billing Section Shell */}
                    {activeTab === "Billing & Plans" && (
                         <div className="bg-zinc-900 border border-zinc-800 rounded-[40px] p-12 text-white relative overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-500">
                             <div className="relative z-10 space-y-8">
                                <div className="flex items-center justify-between">
                                    <div className="space-y-1">
                                        <h3 className="text-3xl font-black font-display italic tracking-tight">HireSight Professional</h3>
                                        <p className="text-gray-400 font-black uppercase tracking-[0.2em] text-[10px]">Current Plan: Free Tier</p>
                                    </div>
                                    <div className="p-4 bg-white/10 rounded-[28px] text-primary">
                                        <Zap className="w-8 h-8" />
                                    </div>
                                </div>
                                <div className="p-8 bg-white/5 rounded-[32px] border border-white/5 backdrop-blur-sm">
                                    <p className="text-sm text-gray-300 font-bold leading-relaxed mb-6">
                                        Unlock the full power of our <span className="text-primary italic">Neural Matching Engine</span>. Post unlimited jobs, extract deep candidate metrics, and automate 90% of your screening pipeline.
                                    </p>
                                    <button className="w-full py-5 bg-primary text-white rounded-[24px] font-black text-lg uppercase tracking-widest italic shadow-2xl hover:scale-[1.02] transition-all">Upgrade Protocol</button>
                                </div>
                             </div>
                             <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_100%_0%,rgba(0,102,255,0.1),transparent)] pointer-events-none" />
                         </div>
                    )}
                </div>
            </div>
        </div>
    );
}
