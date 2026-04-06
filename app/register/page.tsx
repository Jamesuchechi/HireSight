"use client";

import { useState, Suspense } from "react";
import { motion } from "framer-motion";
import { User, Building2, Eye, EyeOff, Loader2, Rocket, ArrowRight } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { useRouter, useSearchParams } from "next/navigation";

function RegisterForm() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const supabase = createClient();

    const [role, setRole] = useState<"candidate" | "recruiter">(
        (searchParams.get("role") as "candidate" | "recruiter") || "candidate"
    );
    const [fullName, setFullName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const { error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName,
                    role: role,
                },
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
        });

        if (error) {
            setError(error.message);
            setLoading(false);
        } else {
            router.push("/login?message=Check your email to confirm your account");
        }
    };

    return (
        <div className="min-h-screen flex selection:bg-primary/20 selection:text-primary overflow-hidden">
            {/* Left Side: Illustration & Branding */}
            <div className="hidden lg:flex w-1/2 bg-zinc-900 relative items-center justify-center p-12 overflow-hidden">
                <div className="absolute inset-0 z-0">
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(0,102,255,0.1),transparent)] blur-3xl shadow-2xl" />
                </div>
                
                <div className="relative z-10 max-w-md">
                    <Link href="/" className="inline-flex items-center space-x-3 mb-12">
                        <div className="w-10 h-10 rounded-xl overflow-hidden shadow-2xl">
                             <img src="/logo.png" alt="HireSight Logo" className="w-full h-full object-cover scale-[1.3]" />
                        </div>
                        <span className="font-display text-2xl font-black text-white tracking-widest">HIRESIGHT</span>
                    </Link>
                    
                    <motion.h2 
                        className="text-4xl md:text-5xl font-black font-display text-white mb-6 leading-tight italic"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                    >
                        Join the future of <br />
                        <span className="text-secondary italic underline decoration-white/20">intelligent hiring.</span>
                    </motion.h2>
                    <p className="text-lg text-gray-400 mb-8 leading-relaxed">
                        Whether you are a world-class talent or a high-velocity recruiter, HireSight is your unfair advantage.
                    </p>
                    
                    <div className="space-y-6">
                        {[
                            { title: "Sub-second AI Matching", desc: "Groq™ powered engine." },
                            { title: "Bias-Free Evaluation", desc: "Merit-based algorithms." },
                            { title: "Deep Analytics", desc: "Skills & gap metrics natively." }
                        ].map((item, i) => (
                            <motion.div 
                                key={i}
                                className="flex items-center space-x-4"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 + 0.5 }}
                            >
                                <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center text-primary">
                                    <Rocket className="w-4 h-4" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-white text-sm">{item.title}</h4>
                                    <p className="text-xs text-gray-500">{item.desc}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
                
                {/* Visual Ornament */}
                <div className="absolute -bottom-20 -right-20 w-96 h-96 bg-primary/10 blur-[120px] rounded-full animate-pulse" />
            </div>

            {/* Right Side: Register Form */}
            <div className="w-full lg:w-1/2 bg-white flex flex-col justify-center p-8 sm:p-12 lg:p-24 overflow-y-auto">
                <div className="max-w-md mx-auto w-full">
                    <div className="mb-10 lg:hidden">
                        <Link href="/" className="inline-flex items-center space-x-3 mb-12">
                            <div className="w-8 h-8 rounded-lg overflow-hidden shadow-xl">
                                <img src="/logo.png" alt="Logo" className="w-full h-full object-cover scale-150" />
                            </div>
                            <span className="font-display text-xl font-black text-zinc-900 tracking-widest">HIRESIGHT</span>
                        </Link>
                    </div>

                    <div className="mb-10">
                        <h1 className="text-4xl font-black font-display text-zinc-900 mb-2 italic tracking-tight">Access Granted</h1>
                        <p className="text-gray-500 font-bold">Create your professional profile on HireSight v2.</p>
                    </div>

                    {/* Role Selector */}
                    <div className="grid grid-cols-2 gap-4 mb-8">
                        <button 
                            onClick={() => setRole("candidate")}
                            className={`p-4 rounded-2xl border-2 flex flex-col items-center justify-center space-y-2 transition-all ${
                                role === 'candidate' ? 'border-primary bg-primary/5 text-primary' : 'border-gray-100 bg-gray-50 text-gray-400 hover:border-gray-200'
                            }`}
                        >
                            <User className="w-5 h-5" />
                            <span className="text-xs font-black uppercase tracking-widest">Job Seeker</span>
                        </button>
                        <button 
                            onClick={() => setRole("recruiter")}
                            className={`p-4 rounded-2xl border-2 flex flex-col items-center justify-center space-y-2 transition-all ${
                                role === 'recruiter' ? 'border-secondary bg-secondary/5 text-secondary' : 'border-gray-100 bg-gray-50 text-gray-400 hover:border-gray-200'
                            }`}
                        >
                            <Building2 className="w-5 h-5" />
                            <span className="text-xs font-black uppercase tracking-widest">Recruiter</span>
                        </button>
                    </div>

                    <form onSubmit={handleRegister} className="space-y-6">
                        <div>
                            <label className="block text-xs font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Full Name</label>
                            <input 
                                required
                                type="text" 
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full p-4 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder={role === 'candidate' ? "e.g. Sarah Chen" : "e.g. Lead Talent Acq."}
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Work Email</label>
                            <input 
                                required
                                type="email" 
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full p-4 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder="name@company.com"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Create Password</label>
                            <div className="relative">
                                <input 
                                    required
                                    type={showPassword ? "text" : "password"} 
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full p-4 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300 pr-12"
                                    placeholder="••••••••"
                                />
                                <button 
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                >
                                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        {error && (
                            <div className="p-4 bg-red-50 border border-red-100 text-red-600 rounded-2xl text-sm font-bold flex items-center space-x-2">
                                <div className="w-1 h-1 bg-red-600 rounded-full" />
                                <span>{error}</span>
                            </div>
                        )}

                        <button 
                            disabled={loading}
                            className="w-full py-5 bg-zinc-900 text-white rounded-2xl font-black text-lg shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center space-x-3 disabled:opacity-50 group"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    <span>Initialize Access</span>
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-10 pt-8 border-t border-gray-100 text-center">
                        <p className="text-gray-500 font-bold">Already a member? <Link href="/login" className="text-primary hover:underline">Secure Login</Link></p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function Register() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-white"><Loader2 className="w-10 h-10 animate-spin text-primary" /></div>}>
            <RegisterForm />
        </Suspense>
    );
}
