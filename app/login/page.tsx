"use client";

import { useState, Suspense } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2, Key, ArrowRight } from "lucide-react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { useRouter, useSearchParams } from "next/navigation";

function LoginForm() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const supabase = createClient();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(searchParams.get("message"));

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setMessage(null);

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            setError(error.message);
            setLoading(false);
        } else {
            router.push("/dashboard");
        }
    };

    return (
        <div className="min-h-screen flex selection:bg-primary/20 selection:text-primary overflow-hidden">
            {/* Left Side: Branding */}
            <div className="hidden lg:flex w-1/2 bg-zinc-900 relative items-center justify-center p-12 overflow-hidden">
                <div className="absolute inset-0 z-0">
                    <div className="absolute top-0 right-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,rgba(0,102,255,0.1),transparent)] blur-3xl shadow-2xl opacity-50" />
                </div>
                
                <div className="relative z-10 max-w-sm">
                    <Link href="/" className="inline-flex items-center space-x-3 mb-16">
                        <div className="w-10 h-10 rounded-xl overflow-hidden shadow-2xl">
                             <img src="/logo.png" alt="HireSight Logo" className="w-full h-full object-cover scale-[1.3]" />
                        </div>
                        <span className="font-display text-2xl font-black text-white tracking-widest">HIRESIGHT</span>
                    </Link>
                    
                    <motion.h2 
                        className="text-4xl md:text-5xl font-black font-display text-white mb-8 leading-tight italic"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                    >
                        Secure <br />
                        <span className="text-primary italic underline decoration-white/20">Authenticated</span> Access.
                    </motion.h2>
                    <p className="text-lg text-gray-400 mb-10 leading-relaxed font-medium">
                        Welcome back. Log in to manage your career or your recruitment pipeline with AI precision.
                    </p>
                    
                    <div className="p-8 bg-white/5 border border-white/10 rounded-[32px] backdrop-blur-xl">
                        <div className="flex items-center space-x-3 mb-4">
                            <Key className="w-5 h-5 text-primary" />
                            <h4 className="text-sm font-black text-white uppercase tracking-widest">Encrypted Auth</h4>
                        </div>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            Your session is secured with military-grade encryption and Supabase Row-Level Security.
                        </p>
                    </div>
                </div>
                
                {/* Visual Ornament */}
                <div className="absolute top-1/4 left-[-10%] w-80 h-80 bg-primary/10 blur-[100px] rounded-full animate-pulse" />
            </div>

            {/* Right Side: Login Form */}
            <div className="w-full lg:w-1/2 bg-white flex flex-col justify-center p-8 sm:p-12 lg:p-24 overflow-y-auto">
                <div className="max-w-md mx-auto w-full">
                    <div className="mb-10 lg:hidden text-center">
                        <Link href="/" className="inline-flex items-center space-x-3 mb-6">
                            <div className="w-8 h-8 rounded-lg overflow-hidden shadow-xl">
                                <img src="/logo.png" alt="Logo" className="w-full h-full object-cover scale-150" />
                            </div>
                            <span className="font-display text-xl font-black text-zinc-900 tracking-widest">HIRESIGHT</span>
                        </Link>
                    </div>

                    <div className="mb-12">
                        <h1 className="text-4xl font-black font-display text-zinc-900 mb-2 italic tracking-tight">Security Check</h1>
                        <p className="text-gray-500 font-bold">Please authenticate to access your dashboard.</p>
                    </div>

                    {message && (
                        <div className="p-4 bg-emerald-50 border border-emerald-100 text-emerald-600 rounded-2xl text-sm font-bold flex items-center space-x-2 mb-8">
                            <div className="w-1.5 h-1.5 bg-emerald-600 rounded-full animate-pulse" />
                            <span>{message}</span>
                        </div>
                    )}

                    <form onSubmit={handleLogin} className="space-y-6">
                        <div>
                            <label className="block text-xs font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Work Email</label>
                            <input 
                                required
                                type="email" 
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300"
                                placeholder="name@company.com"
                            />
                        </div>
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-xs font-black uppercase tracking-[0.2em] text-gray-400">Password</label>
                                <Link href="#" className="text-[10px] uppercase tracking-widest font-black text-primary hover:underline">Forgot Access Key?</Link>
                            </div>
                            <div className="relative">
                                <input 
                                    required
                                    type={showPassword ? "text" : "password"} 
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full p-5 bg-gray-50 border-2 border-transparent rounded-2xl focus:border-primary/20 focus:bg-white outline-none transition-all font-bold placeholder:text-gray-300 pr-12"
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
                                <div className="w-1.5 h-1.5 bg-red-600 rounded-full" />
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
                                    <span>Secure Login</span>
                                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className="mt-12 pt-8 border-t border-gray-100 text-center">
                        <p className="text-gray-500 font-bold">New operative? <Link href="/register" className="text-primary hover:underline">Request Access</Link></p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function Login() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center bg-white"><Loader2 className="w-10 h-10 animate-spin text-primary" /></div>}>
            <LoginForm />
        </Suspense>
    );
}
