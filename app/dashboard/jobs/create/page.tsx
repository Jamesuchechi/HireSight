"use client";

import JobForm from "@/components/jobs/JobForm";
import { ArrowLeft, Rocket } from "lucide-react";
import Link from "next/link";
import { motion } from "framer-motion";

export default function NewJobPage() {
    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-20">
            {/* Navigation & Header */}
            <header className="flex flex-col space-y-6">
                <Link 
                    href="/dashboard/jobs" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors group"
                >
                    <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Fleet</span>
                </Link>

                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
                    <div>
                        <div className="flex items-center space-x-4 mb-4">
                            <div className="p-3 bg-primary/10 text-primary rounded-[20px]">
                                <Rocket className="w-6 h-6" />
                            </div>
                            <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">Mission Deployment</span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                            Protocol <span className="text-primary tracking-normal font-body">Initialization</span>
                        </h1>
                    </div>
                </div>
            </header>

            {/* Form Container */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
            >
                <JobForm />
            </motion.div>

            {/* Footer Tip */}
            <div className="bg-zinc-900 rounded-[40px] p-10 flex flex-col md:flex-row items-center justify-between gap-8 overflow-hidden relative">
                <div className="relative z-10 space-y-2">
                    <h4 className="text-2xl font-black text-white italic tracking-tight">Need AI assistance?</h4>
                    <p className="text-gray-400 font-bold max-w-sm text-xs leading-relaxed italic">Our Hiresight-powered engine can help you refine your job title and description in real-time as you type.</p>
                </div>
                <button className="relative z-10 px-8 py-4 bg-primary text-white rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-[1.05] transition-all">
                    Enable AI Copilot
                </button>
                <div className="absolute right-0 top-0 w-64 h-64 bg-primary/20 blur-[100px] rounded-full pointer-events-none" />
            </div>
        </div>
    );
}
