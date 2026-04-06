"use client";

import { useState, useEffect, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Building2, MapPin, Target, FileText, CheckCircle2, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

function OnboardingForm() {
    const router = useRouter();
    const supabase = createClient();
    
    const [step, setStep] = useState(1);
    const [role, setRole] = useState<"candidate" | "recruiter" | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    
    // Form fields
    const [fullName, setFullName] = useState("");
    const [location, setLocation] = useState("");
    const [bio, setBio] = useState("");
    const [industry, setIndustry] = useState("");
    const [company, setCompany] = useState("");

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
                if (profile.onboarding_completed) {
                    router.push("/dashboard");
                    return;
                }
                setRole(profile.role);
                setFullName(profile.full_name || "");
            }
            setLoading(false);
        };
        fetchProfile();
    }, [supabase, router]);

    const handleSubmit = async () => {
        setSubmitting(true);
        const { data: { user } } = await supabase.auth.getUser();
        
        const updateData = {
            full_name: fullName,
            onboarding_completed: true,
        };

        const { error } = await supabase
            .from("profiles")
            .update(updateData)
            .eq("id", user?.id);

        if (!error) {
            router.push("/dashboard");
        } else {
            console.error(error);
            setSubmitting(false);
        }
    };

    if (loading) return null;

    const totalSteps = 3;

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6 selection:bg-primary/20 selection:text-primary">
            {/* Background Ornaments */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full" />
                <div className="absolute bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-secondary/5 blur-[100px] rounded-full" />
            </div>

            <div className="w-full max-w-2xl bg-white border border-gray-100 rounded-[48px] shadow-2xl relative overflow-hidden">
                {/* Progress Bar */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gray-100">
                    <motion.div 
                        className="h-full bg-primary"
                        initial={{ width: 0 }}
                        animate={{ width: `${(step / totalSteps) * 100}%` }}
                    />
                </div>

                <div className="p-12 md:p-20">
                    <AnimatePresence mode="wait">
                        {step === 1 && (
                            <motion.div 
                                key="step1"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-8"
                            >
                                <div className="space-y-4">
                                    <div className="inline-flex items-center space-x-2 px-3 py-1 bg-primary/10 rounded-full">
                                        <Sparkles className="w-3 h-3 text-primary" />
                                        <span className="text-[10px] font-black text-primary uppercase tracking-widest">Initialization</span>
                                    </div>
                                    <h2 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight">Confirm Identity</h2>
                                    <p className="text-gray-500 font-bold leading-relaxed">Let's verify your professional details for the HireSight protocol.</p>
                                </div>

                                <div className="space-y-6">
                                    <div>
                                        <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Display Name</label>
                                        <div className="relative">
                                            <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
                                            <input 
                                                type="text" 
                                                value={fullName}
                                                onChange={(e) => setFullName(e.target.value)}
                                                className="w-full pl-12 pr-6 py-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                                placeholder="Your full name"
                                            />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Current Location</label>
                                        <div className="relative">
                                            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
                                            <input 
                                                type="text" 
                                                value={location}
                                                onChange={(e) => setLocation(e.target.value)}
                                                className="w-full pl-12 pr-6 py-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                                placeholder="City, Country"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        {step === 2 && (
                            <motion.div 
                                key="step2"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-8"
                            >
                                <div className="space-y-4">
                                     <div className="inline-flex items-center space-x-2 px-3 py-1 bg-secondary/10 rounded-full">
                                        <Target className="w-3 h-3 text-secondary" />
                                        <span className="text-[10px] font-black text-secondary uppercase tracking-widest">Professional Context</span>
                                    </div>
                                    <h2 className="text-4xl font-black font-display text-zinc-900 italic tracking-tight">
                                        {role === 'recruiter' ? "About Your Team" : "About Your Career"}
                                    </h2>
                                    <p className="text-gray-500 font-bold leading-relaxed">This data helps our AI matching engine prioritize your {role === 'recruiter' ? "hiring" : "growth"}.</p>
                                </div>

                                <div className="space-y-6">
                                    {role === 'recruiter' ? (
                                        <>
                                            <div>
                                                <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Company / Organization</label>
                                                <div className="relative">
                                                    <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-300" />
                                                    <input 
                                                        type="text"
                                                        value={company}
                                                        onChange={(e) => setCompany(e.target.value)}
                                                        className="w-full pl-12 pr-6 py-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-secondary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                                        placeholder="Company name"
                                                    />
                                                </div>
                                            </div>
                                            <div>
                                                <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Industry Sector</label>
                                                <input 
                                                    type="text"
                                                    value={industry}
                                                    onChange={(e) => setIndustry(e.target.value)}
                                                    className="w-full px-6 py-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-secondary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                                    placeholder="e.g. Fintech, E-commerce, SaaS"
                                                />
                                            </div>
                                        </>
                                    ) : (
                                        <div>
                                            <label className="block text-[10px] font-black uppercase text-gray-400 tracking-widest mb-2">Professional Headline</label>
                                            <textarea 
                                                value={bio}
                                                onChange={(e) => setBio(e.target.value)}
                                                className="w-full px-6 py-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300 h-32 resize-none"
                                                placeholder="Briefly describe your expertise..."
                                            />
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}

                        {step === 3 && (
                            <motion.div 
                                key="step3"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="text-center space-y-10"
                            >
                                <div className="flex flex-col items-center space-y-6">
                                    <div className="w-24 h-24 bg-emerald-50 text-emerald-500 rounded-[32px] flex items-center justify-center animate-bounce shadow-2xl shadow-emerald-500/20">
                                        <CheckCircle2 className="w-12 h-12" />
                                    </div>
                                    <div className="space-y-4">
                                        <h2 className="text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none">All Set!</h2>
                                        <p className="text-gray-500 font-bold max-w-sm mx-auto">Your digital profile is synchronized with the HireSight Neural Engine.</p>
                                    </div>
                                </div>
                                
                                <div className="p-8 bg-zinc-900 rounded-[32px] text-white text-left relative overflow-hidden group">
                                     <div className="relative z-10 flex items-center justify-between">
                                        <div>
                                            <h4 className="text-xl font-black font-display italic leading-none mb-1">Final Authorization</h4>
                                            <p className="text-xs text-gray-500 font-bold uppercase tracking-widest leading-none">Activate your Dashboard</p>
                                        </div>
                                        <div className="p-3 bg-white/10 rounded-2xl">
                                             <FileText className="w-5 h-5 text-primary" />
                                        </div>
                                     </div>
                                     {/* Background glow */}
                                     <div className="absolute -right-10 -bottom-10 w-40 h-40 bg-primary/20 blur-3xl rounded-full group-hover:scale-150 transition-transform duration-1000" />
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    <div className="mt-16 flex items-center justify-between">
                        {step > 1 ? (
                            <button 
                                onClick={() => setStep(step - 1)}
                                className="px-8 py-4 text-sm font-black uppercase text-gray-400 hover:text-zinc-900 transition-colors"
                            >
                                Back
                            </button>
                        ) : (
                            <div />
                        )}
                        
                        <button 
                            disabled={submitting}
                            onClick={() => step < totalSteps ? setStep(step + 1) : handleSubmit()}
                            className="px-10 py-5 bg-zinc-900 text-white rounded-2xl font-black text-lg shadow-2xl hover:scale-[1.03] active:scale-[0.98] transition-all flex items-center justify-center space-x-3 disabled:opacity-50 group min-w-[200px]"
                        >
                            {submitting ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    <span>{step === totalSteps ? "Finish" : "Continue"}</span>
                                    {step < totalSteps && <ArrowRight className="w-5 h-5 group-hover:translate-x-1" />}
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function Onboarding() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-white"><Loader2 className="w-10 h-10 animate-spin text-primary" /></div>}>
            <OnboardingForm />
        </Suspense>
    );
}
