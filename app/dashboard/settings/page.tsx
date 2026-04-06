"use client";

import { useEffect, useState } from "react";
import { User, Shield, Bell, CreditCard, Loader2, Save } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

export default function Settings() {
    const supabase = createClient();
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    
    // Form fields
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");

    useEffect(() => {
        const fetchProfile = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user) {
                setEmail(user.email || "");
                const { data: profile } = await supabase
                    .from("profiles")
                    .select("*")
                    .eq("id", user.id)
                    .single();
                if (profile) {
                    setProfile(profile);
                    setFullName(profile.full_name || "");
                }
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase]);

    const handleSave = async () => {
        setSaving(true);
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            await supabase
                .from("profiles")
                .update({ full_name: fullName })
                .eq("id", user.id);
        }
        setSaving(false);
    };

    if (loading) return null;

    return (
        <div className="max-w-4xl mx-auto space-y-10">
            <header>
                <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight">Account Parameters</h1>
                <p className="text-gray-500 font-bold">Manage your security and professional configuration.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                {/* Sidebar */}
                <div className="space-y-2">
                    {[
                        { icon: <User className="w-4 h-4" />, label: "Profile" },
                        { icon: <Shield className="w-4 h-4" />, label: "Security" },
                        { icon: <Bell className="w-4 h-4" />, label: "Alerts" },
                        { icon: <CreditCard className="w-4 h-4" />, label: "Billing" },
                    ].map((item, i) => (
                        <button key={i} className={`w-full flex items-center space-x-3 px-4 py-3 rounded-2xl text-sm font-black transition-all ${i === 0 ? "bg-white text-primary shadow-sm" : "text-gray-400 hover:text-zinc-900 hover:bg-gray-100"}`}>
                            {item.icon}
                            <span>{item.label}</span>
                        </button>
                    ))}
                </div>

                {/* Main Settings Form */}
                <div className="md:col-span-3 space-y-8">
                    <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10">
                        <div className="flex items-center space-x-6">
                            <div className="w-24 h-24 bg-primary text-white rounded-[32px] flex items-center justify-center text-4xl font-black italic shadow-2xl shadow-primary/20">
                                {fullName?.[0] || 'U'}
                            </div>
                            <div>
                                <button className="px-5 py-2.5 bg-zinc-900 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:scale-[1.03] transition-all">Update Avatar</button>
                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-3">JPG, PNG or WEBP. Max 2MB.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Full Identity</label>
                                <input 
                                    type="text" 
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full p-4 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold"
                                />
                            </div>
                            <div>
                                <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Email Address</label>
                                <input 
                                    disabled
                                    type="email" 
                                    value={email}
                                    className="w-full p-4 bg-gray-100 border-2 border-transparent rounded-2xl font-bold text-gray-400 cursor-not-allowed"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Professional Role</label>
                            <input 
                                disabled
                                type="text" 
                                value={profile?.role || "candidate"}
                                className="w-full p-4 bg-gray-100 border-2 border-transparent rounded-2xl font-bold text-gray-400 uppercase tracking-widest cursor-not-allowed"
                            />
                        </div>

                        <div className="pt-6 border-t border-gray-50 flex justify-end">
                            <button 
                                onClick={handleSave}
                                disabled={saving}
                                className="px-10 py-4 bg-primary text-white rounded-2xl font-black italic shadow-xl hover:scale-[1.03] transition-all flex items-center space-x-2"
                            >
                                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                <span>Save Changes</span>
                            </button>
                        </div>
                    </div>

                    <div className="bg-red-50/50 border border-red-100 rounded-[40px] p-10 flex items-center justify-between">
                         <div>
                            <h4 className="text-xl font-black text-red-600 italic tracking-tight">Danger Zone</h4>
                            <p className="text-xs text-red-400 font-bold uppercase tracking-widest">Permanent account deletion</p>
                         </div>
                         <button className="px-8 py-4 bg-red-600 text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-red-700 transition-all shadow-xl shadow-red-600/20">Deactivate</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
