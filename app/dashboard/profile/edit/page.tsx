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
    ShieldCheck,
    Globe,
    Phone,
    Briefcase,
    BookOpen,
    Target
} from "lucide-react";
import { motion } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import ImageUpload from "@/components/ImageUpload";
import ListEditor from "@/components/profile/ListEditor";
import { ExtendedProfile, Experience, Education, Skill, PortfolioLink } from "@/types/profile";

export default function EditProfile() {
    const router = useRouter();
    const supabase = createClient();
    const [profile, setProfile] = useState<ExtendedProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [success, setSuccess] = useState(false);

    // Form fields
    const [fullName, setFullName] = useState("");
    const [bio, setBio] = useState("");
    const [headline, setHeadline] = useState("");
    const [location, setLocation] = useState("");
    const [phone, setPhone] = useState("");
    const [avatarUrl, setAvatarUrl] = useState("");
    const [coverUrl, setCoverUrl] = useState("");
    
    // Complex fields
    const [skills, setSkills] = useState<Skill[]>([]);
    const [experience, setExperience] = useState<Experience[]>([]);
    const [education, setEducation] = useState<Education[]>([]);
    const [portfolioLinks, setPortfolioLinks] = useState<PortfolioLink[]>([]);

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
                setProfile(profile as ExtendedProfile);
                setFullName(profile.full_name || "");
                setBio(profile.bio || "");
                setHeadline(profile.headline || "");
                setLocation(profile.location || "");
                setPhone(profile.phone || "");
                setAvatarUrl(profile.avatar_url || "");
                setCoverUrl(profile.cover_url || "");
                setSkills(profile.skills || []);
                setExperience(profile.experience || []);
                setEducation(profile.education || []);
                setPortfolioLinks(profile.portfolio_links || []);
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
                    headline: headline,
                    location: location,
                    phone: phone,
                    avatar_url: avatarUrl,
                    cover_url: coverUrl,
                    skills,
                    experience,
                    education,
                    portfolio_links: portfolioLinks
                })
                .eq("id", user.id);

            if (!error) {
                setSuccess(true);
                setTimeout(() => setSuccess(false), 3000);
            }
        }
        setSaving(false);
    };

    if (loading || !profile) return null;

    return (
        <div className="max-w-4xl mx-auto pb-20 px-4 md:px-0">
            {/* Header */}
            <div className="flex items-center justify-between mb-10 mt-8">
                <div className="flex items-center space-x-6">
                    <button 
                        onClick={() => router.back()}
                        className="p-3 bg-white border border-gray-100 rounded-2xl hover:bg-gray-50 transition-all text-zinc-900 shadow-sm"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <div>
                        <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight leading-none uppercase">Refine Identity</h1>
                        <p className="text-gray-500 font-bold uppercase tracking-widest text-[10px] mt-2 leading-none">Protocol Update v3.0 // Final Parity</p>
                    </div>
                </div>
            </div>

            <form onSubmit={handleSave} className="space-y-12">
                {/* Visual Branding Card */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm space-y-10 relative overflow-hidden group">
                    <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[80px] rounded-full pointer-events-none" />
                    
                    <div className="flex items-center space-x-4 mb-2">
                        <ImageIcon className="w-6 h-6 text-primary" />
                        <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Visual Identity</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                        <ImageUpload uid={profile.id} url={avatarUrl} type="avatar" label="Profile Photo" onUpload={setAvatarUrl} />
                        <ImageUpload uid={profile.id} url={coverUrl} type="cover" label="Cover Banner" onUpload={setCoverUrl} />
                    </div>
                </div>

                {/* Core Personal Info Card */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm space-y-8">
                    <div className="flex items-center space-x-4">
                        <User className="w-6 h-6 text-primary" />
                        <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase">Core Logistics</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3 px-2">Full Signature</label>
                            <input 
                                required type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
                                className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder="Your full name"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3 px-2">Professional Headline</label>
                            <input 
                                type="text" value={headline} onChange={(e) => setHeadline(e.target.value)}
                                className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder="e.g. Senior Intelligence Architect"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3 px-2">Current Location</label>
                            <div className="relative">
                                <MapPin className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input 
                                    type="text" value={location} onChange={(e) => setLocation(e.target.value)}
                                    className="w-full pl-14 pr-6 py-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                    placeholder="San Francisco, CA"
                                />
                            </div>
                        </div>
                        <div>
                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3 px-2">Comms Channel (Phone)</label>
                            <div className="relative">
                                <Phone className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input 
                                    type="text" value={phone} onChange={(e) => setPhone(e.target.value)}
                                    className="w-full pl-14 pr-6 py-5 bg-gray-50 border-2 border-transparent rounded-[24px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                    placeholder="+1 (555) 000-0000"
                                />
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-3 px-2">Operational Summary (Bio)</label>
                        <div className="relative">
                            <FileText className="absolute left-6 top-6 w-5 h-5 text-gray-400" />
                            <textarea 
                                value={bio} onChange={(e) => setBio(e.target.value)}
                                className="w-full pl-16 pr-8 pt-5 bg-gray-50 border-2 border-transparent rounded-[32px] focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300 h-40 resize-none"
                                placeholder="Synthesize your professional history and mission..."
                            />
                        </div>
                    </div>
                </div>

                {/* Professional History / Experience */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm">
                    <ListEditor<Experience>
                        title="Operative Log (Experience)"
                        items={experience}
                        onUpdate={setExperience}
                        fields={[
                            { key: "role", label: "Role", type: "text", placeholder: "Senior Operative" },
                            { key: "company", label: "Organization", type: "text", placeholder: "Protocol-X" },
                            { key: "start_date", label: "Commencement", type: "text", placeholder: "YYYY-MM" },
                            { key: "end_date", label: "Termination", type: "text", placeholder: "YYYY-MM" },
                            { key: "current", label: "Active Protocol", type: "checkbox" },
                            { key: "description", label: "Mission Briefing", type: "textarea", placeholder: "Achievements and responsibilities..." }
                        ]}
                        newItemTemplate={{ role: "", company: "", start_date: "", end_date: "", current: false, description: "" }}
                        renderItem={(item) => (
                            <div className="flex items-start space-x-4">
                                <Briefcase className="w-8 h-8 text-primary shrink-0 mt-1" />
                                <div>
                                    <p className="font-black italic text-zinc-900">{item.role} @ {item.company}</p>
                                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{item.start_date} - {item.current ? "PRESENT" : item.end_date}</p>
                                </div>
                            </div>
                        )}
                    />
                </div>

                 {/* Skills Matrix */}
                 <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm">
                    <ListEditor<Skill>
                        title="Competency Matrix (Skills)"
                        items={skills}
                        onUpdate={setSkills}
                        fields={[
                            { key: "skill", label: "Skill / Protocol", type: "text", placeholder: "Next.js, Stealth, etc." },
                            { 
                                key: "proficiency", 
                                label: "Proficiency Level", 
                                type: "select", 
                                options: [
                                    { value: "expert", label: "Expert / Lead" },
                                    { value: "advanced", label: "Advanced" },
                                    { value: "intermediate", label: "Intermediate" },
                                    { value: "beginner", label: "Beginner" }
                                ] 
                            }
                        ]}
                        newItemTemplate={{ skill: "", proficiency: "intermediate" }}
                        renderItem={(item) => (
                            <div className="flex items-center space-x-4">
                                <Target className="w-8 h-8 text-secondary shrink-0" />
                                <div>
                                    <p className="font-black italic text-zinc-900 uppercase tracking-wider">{item.skill}</p>
                                    <p className="text-[10px] font-bold text-primary uppercase tracking-widest">{item.proficiency}</p>
                                </div>
                            </div>
                        )}
                    />
                </div>

                 {/* Education */}
                 <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm">
                    <ListEditor<Education>
                        title="Academic Archives (Education)"
                        items={education}
                        onUpdate={setEducation}
                        fields={[
                            { key: "institution", label: "Institution", type: "text", placeholder: "Stanford Academy" },
                            { key: "degree", label: "Degree / Ranking", type: "text", placeholder: "B.S. Intelligence" },
                            { key: "field", label: "Field of Study", type: "text", placeholder: "Computer Science" },
                            { key: "end_year", label: "Acquisition Year", type: "number", placeholder: "2024" }
                        ]}
                        newItemTemplate={{ institution: "", degree: "", field: "", start_year: 2020, end_year: 2024 }}
                        renderItem={(item) => (
                            <div className="flex items-center space-x-4">
                                <BookOpen className="w-8 h-8 text-zinc-400 shrink-0" />
                                <div>
                                    <p className="font-black italic text-zinc-900">{item.degree} in {item.field}</p>
                                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{item.institution} // Class of {item.end_year}</p>
                                </div>
                            </div>
                        )}
                    />
                </div>

                {/* Identity Links */}
                <div className="bg-white border border-gray-100 rounded-[40px] p-6 md:p-12 shadow-sm">
                    <ListEditor<PortfolioLink>
                        title="Identity Proxies (Links)"
                        items={portfolioLinks}
                        onUpdate={setPortfolioLinks}
                        fields={[
                            { 
                                key: "type", 
                                label: "Proxy Type", 
                                type: "select", 
                                options: [
                                    { value: "github", label: "GitHub" },
                                    { value: "linkedin", label: "LinkedIn" },
                                    { value: "portfolio", label: "Personal Dossier" },
                                    { value: "twitter", label: "Twitter" },
                                    { value: "other", label: "Other Binary Link" }
                                ] 
                            },
                            { key: "url", label: "Link Address", type: "text", placeholder: "https://..." }
                        ]}
                        newItemTemplate={{ type: "portfolio", url: "" }}
                        renderItem={(item) => (
                            <div className="flex items-center space-x-4">
                                <Globe className="w-8 h-8 text-primary shrink-0" />
                                <div>
                                    <p className="font-black italic text-zinc-900 uppercase tracking-wider">{item.type}</p>
                                    <p className="text-[10px] font-bold text-gray-400 truncate max-w-[200px]">{item.url}</p>
                                </div>
                            </div>
                        )}
                    />
                </div>

                {/* Save Section */}
                <div className="flex items-center justify-between pt-8 sticky bottom-10 z-10">
                    <div className="flex items-center space-x-2">
                        {success && (
                            <motion.div 
                                initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                                className="flex items-center space-x-2 text-emerald-600 bg-emerald-50 px-6 py-4 rounded-[24px] border border-emerald-100 shadow-xl"
                            >
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="font-black italic text-xs uppercase tracking-widest">Protocol Sync Complete</span>
                            </motion.div>
                        )}
                    </div>

                    <button 
                        type="submit" disabled={saving}
                        className="px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black text-lg uppercase tracking-widest italic shadow-2xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center space-x-4 disabled:opacity-50 border-b-4 border-primary"
                    >
                        {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5 text-primary" />}
                        <span>Publish Updates</span>
                    </button>
                </div>
            </form>
        </div>
    );
}
