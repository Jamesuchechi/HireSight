"use client";

import { useEffect, useState } from "react";
import { 
    User, 
    Image as ImageIcon, 
    FileText, 
    MapPin, 
    Save, 
    Loader2, 
    ArrowLeft,
    CheckCircle2,
    ShieldCheck
} from "lucide-react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import ImageUpload from "@/components/ImageUpload";
import Link from "next/link";

export default function EditProfile() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);

    // Form fields
    const [fullName, setFullName] = useState("");
    const [bio, setBio] = useState("");
    const [avatarUrl, setAvatarUrl] = useState("");
    const [coverUrl, setCoverUrl] = useState("");
    const [role, setRole] = useState("");

    useEffect(() => {
        const fetchProfile = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            const { data: profile } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            if (profile) {
                setProfile(profile);
                setFullName(profile.full_name || "");
                setBio(profile.bio || "");
                setAvatarUrl(profile.avatar_url || "");
                setCoverUrl(profile.cover_url || "");
                setRole(profile.role || "");
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase, router]);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        setSuccess(false);

        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            const { error } = await supabase
                .from("profiles")
                .update({
                    full_name: fullName,
                    bio: bio,
                    avatar_url: avatarUrl,
                    cover_url: coverUrl,
                })
                .eq("id", user.id);

            if (!error) {
                setSuccess(true);
                setTimeout(() => setSuccess(false), 3000);
            }
        }
        setSaving(false);
    };

    if (loading) return null;

    return (
        <div className="max-w-4xl mx-auto pb-20">
            {/* Header */}
            <div className="flex items-center justify-between mb-10">
                <div className="flex items-center space-x-6">
                    <button 
                        onClick={() => router.back()}
                        className="p-3 bg-white border border-gray-100 rounded-2xl hover:bg-gray-50 transition-all text-zinc-900"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight leading-none uppercase">Modify Identity</h1>
                        <p className="text-gray-500 font-bold uppercase tracking-widest text-[10px] mt-2 leading-none">Protocol Update v2.0</p>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSave} className="space-y-8">
                {/* Visual Branding Card */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10 relative overflow-hidden group">
                     {/* Abstract BG Decoration */}
                    <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[80px] rounded-full pointer-events-none group-hover:scale-125 transition-transform duration-1000" />
                    
                    <div className="flex items-center space-x-4 mb-2">
                        <ImageIcon className="w-6 h-6 text-primary" />
                        <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Visual Assets</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        {/* Avatar Upload */}
                        <ImageUpload 
                            uid={profile.id}
                            url={avatarUrl}
                            type="avatar"
                            label="Profile Photo"
                            onUpload={(url) => setAvatarUrl(url)}
                        />

                        {/* Cover Upload */}
                        <ImageUpload 
                            uid={profile.id}
                            url={coverUrl}
                            type="cover"
                            label="Cover Banner"
                            onUpload={(url) => setCoverUrl(url)}
                        />
                    </div>
                </div>

                {/* Identity Information Card */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm space-y-10">
                    <div className="flex items-center space-x-4 mb-2">
                        <User className="w-6 h-6 text-primary" />
                        <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Core Identity</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-4">Display Name</label>
                            <input 
                                required
                                type="text" 
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder="Your full name"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-4">Professional Role</label>
                            <div className="relative">
                                <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-emerald-500" />
                                <input 
                                    disabled
                                    type="text" 
                                    value={role}
                                    className="w-full pl-12 pr-6 py-5 bg-emerald-50/50 border-2 border-emerald-100/20 rounded-[24px] font-black uppercase text-emerald-600 tracking-widest text-xs cursor-not-allowed"
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-4">Professional Bio / Summary</label>
                        <div className="relative">
                            <FileText className="absolute left-6 top-6 w-5 h-5 text-gray-400" />
                            <textarea 
                                value={bio}
                                onChange={(e) => setBio(e.target.value)}
                                className="w-full pl-16 pr-8 pt-5 bg-gray-50 border-2 border-transparent rounded-[32px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300 h-48 resize-none"
                                placeholder="Briefly describe your expertise, achievements and professional mission..."
                            />
                        </div>
                    </div>
                </div>

                {/* Save Section */}
                <div className="flex items-center justify-between pt-4">
                    <div className="flex items-center space-x-2">
                        {success && (
                            <motion.div 
                                initial={{ opacity: 0, x: -10 }} 
                                animate={{ opacity: 1, x: 0 }}
                                className="flex items-center space-x-2 text-emerald-600 bg-emerald-50 px-5 py-3 rounded-2xl border border-emerald-100"
                            >
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="font-black italic text-xs uppercase tracking-widest">Protocol Sync Complete</span>
                            </motion.div>
                        )}
                    </div>

                    <button 
                        type="submit"
                        disabled={saving}
                        className="px-12 py-5 bg-zinc-900 text-white rounded-[28px] font-black text-lg uppercase tracking-widest italic shadow-2xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center space-x-3 disabled:opacity-50"
                    >
                        {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5 text-primary" />}
                        <span>Publish Updates</span>
                    </button>
                </div>
            </form>
        </div>
    );
}
