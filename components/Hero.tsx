"use client";

import { useRef, useState, useEffect } from "react";
import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import { ArrowRight, Sparkles, Wand2, Shield, Zap, Users } from "lucide-react";
import Link from "next/link";

const words = ["Intelligent", "Efficiency", "Precision", "Success"];

const Hero = () => {
    const containerRef = useRef<HTMLElement>(null);
    const [index, setIndex] = useState(0);

    const { scrollYProgress } = useScroll({
        target: containerRef,
        offset: ["start start", "end start"],
    });

    const y = useTransform(scrollYProgress, [0, 1], [0, 200]);
    const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);
    const scale = useTransform(scrollYProgress, [0, 0.5], [1, 0.9]);

    useEffect(() => {
        const interval = setInterval(() => {
            setIndex((prev) => (prev + 1) % words.length);
        }, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <section ref={containerRef} className="relative min-h-screen flex items-center justify-center pt-32 pb-40 overflow-hidden">
            {/* Parallax Mesh Background */}
            <motion.div style={{ y, opacity }} className="absolute inset-0 z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[120px] rounded-full animate-pulse" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-secondary/20 blur-[100px] rounded-full animate-bounce [animation-duration:10s]" />
                <div className="absolute top-[20%] right-[10%] w-[30%] h-[30%] bg-accent/10 blur-[80px] rounded-full animate-pulse [animation-delay:2s]" />
                
                {/* Thin grid overlay */}
                <div className="absolute inset-0 bg-[url('/noise.svg')] opacity-20" />
                <div 
                    className="absolute inset-0 opacity-[0.03]" 
                    style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #000 1px, transparent 0)', backgroundSize: '40px 40px' }} 
                />
            </motion.div>

            <div className="relative z-10 max-w-7xl mx-auto px-6 lg:px-8 text-center pt-10">
                <motion.div
                    style={{ scale }}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                >
                    {/* Badge */}
                    <div className="inline-flex items-center space-x-2 px-4 py-2 bg-white/50 backdrop-blur-md border border-gray-200/50 rounded-full mb-10 shadow-sm">
                        <Sparkles className="w-4 h-4 text-primary" />
                        <span className="text-xs font-black uppercase tracking-widest bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                            Next-Gen AI Protocol v3.5
                        </span>
                    </div>

                    {/* Headline with Typewriter */}
                    <h1 className="text-6xl md:text-[110px] font-black font-display text-zinc-900 leading-[0.95] tracking-tighter mb-10">
                        The Future of <br />
                        <div className="relative h-[1.1em] overflow-hidden">
                            <AnimatePresence mode="wait"><motion.span
                                    key={words[index]}
                                    initial={{ y: 50, opacity: 0 }}
                                    animate={{ y: 0, opacity: 1 }}
                                    exit={{ y: -50, opacity: 0 }}
                                    transition={{ duration: 0.5, ease: "circOut" }}
                                    className="absolute inset-0 bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent italic px-2"
                                >{words[index]}</motion.span></AnimatePresence>
                        </div>
                        <span className="text-zinc-900">Hiring</span>
                    </h1>

                    {/* Subheadline */}
                    <p className="max-w-2xl mx-auto text-xl text-gray-600 mb-14 leading-relaxed font-medium">
                        Elevate your recruitment pipeline with sub-second AI inference on <span className="text-zinc-900 font-bold border-b-4 border-primary/20">Hiresight-AI™</span>. Precision matching, zero bias, and infinite scalability.
                    </p>

                    {/* Action Buttons */}
                    <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4 mb-20">
                        <Link
                            href="/register"
                            className="w-full sm:w-auto px-12 py-5 bg-primary text-white rounded-2xl font-black text-lg shadow-2xl shadow-primary/40 hover:scale-[1.03] active:scale-[0.97] transition-all flex items-center justify-center space-x-3 group"
                        >
                            <span>Start Free Trial</span>
                            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </Link>
                        <Link
                            href="#how-it-works"
                            className="w-full sm:w-auto px-12 py-5 bg-white border border-gray-200 text-gray-700 rounded-2xl font-black text-lg hover:bg-gray-50 transition-all flex items-center justify-center space-x-3"
                        >
                            <Wand2 className="w-5 h-5" />
                            <span>See how it works</span>
                        </Link>
                    </div>

                    {/* Meta/Trust badges */}
                    <div className="flex flex-wrap items-center justify-center gap-10 opacity-50 grayscale hover:grayscale-0 transition-all duration-700">
                        <div className="flex items-center space-x-2">
                            <Shield className="w-5 h-5 text-emerald-500" />
                            <span className="text-xs font-black uppercase tracking-widest text-gray-500">GDPR Compliant</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Zap className="w-5 h-5 text-secondary" />
                            <span className="text-xs font-black uppercase tracking-widest text-gray-500">Sub-second Logic</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Users className="w-5 h-5 text-accent" />
                            <span className="text-xs font-black uppercase tracking-widest text-gray-500">Bias-Free Algo</span>
                        </div>
                    </div>
                </motion.div>
            </div>
            
            {/* Enhanced Parallax Preview */}
            <motion.div 
                style={{ y: useTransform(scrollYProgress, [0, 1], [0, -100]) }}
                className="absolute -bottom-20 left-1/2 -translate-x-1/2 w-full max-w-6xl px-6 lg:px-8 hidden md:block"
                initial={{ opacity: 0, y: 100 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 1.2, ease: "easeOut" }}
            >
                <div className="relative p-2 bg-gradient-to-br from-white/30 to-white/10 backdrop-blur-3xl border border-white/20 rounded-[40px] shadow-[0_48px_160px_rgba(0,102,255,0.2)]">
                    <img 
                        src="https://images.unsplash.com/photo-1551434678-e076c223a692?q=80&w=2070&auto=format&fit=crop" 
                        alt="HireSight Interface" 
                        className="w-full h-auto rounded-[32px] rounded-b-none opacity-90 brightness-110"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-white via-white/50 to-transparent bottom-0 h-40" />
                </div>
            </motion.div>
        </section>
    );
};

export default Hero;
