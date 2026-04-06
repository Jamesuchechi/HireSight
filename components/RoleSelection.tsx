"use client";

import { motion } from "framer-motion";
import { User, Building2, ChevronRight, Sparkles, Target } from "lucide-react";
import Link from "next/link";

const RoleSelection = () => {
    return (
        <section className="py-32 bg-white relative">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* For Candidates */}
                    <motion.div
                        className="group relative p-12 bg-gray-50 border border-gray-100 rounded-[48px] overflow-hidden hover:shadow-2xl transition-all duration-500"
                        initial={{ opacity: 0, x: -50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                    >
                        <div className="relative z-10">
                            <div className="w-16 h-16 bg-primary/10 text-primary rounded-3xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                                <User className="w-8 h-8" />
                            </div>
                            <h3 className="text-4xl font-black font-display text-zinc-900 mb-4 italic">For Job Seekers</h3>
                            <p className="text-lg text-gray-500 mb-8 max-w-md">
                                Get matched with roles that actually fit your skills. No more generic applications. No more black holes.
                            </p>
                            <ul className="space-y-4 mb-10">
                                {["AI-Enhanced Profile Builder", "Skill Gap Analysis", "Real-time Application Tracking"].map((item) => (
                                    <li key={item} className="flex items-center space-x-3 text-sm font-bold text-gray-700">
                                        <Sparkles className="w-4 h-4 text-primary" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <Link
                                href="/register?role=candidate"
                                className="inline-flex items-center space-x-3 px-8 py-4 bg-primary text-white rounded-2xl font-black shadow-xl shadow-primary/30 hover:scale-[1.05] active:scale-[0.98] transition-all"
                            >
                                <span>Create Profile</span>
                                <ChevronRight className="w-5 h-5 group-hover:translate-x-1" />
                            </Link>
                        </div>
                        {/* Abstract background shape */}
                        <div className="absolute top-1/2 right-[-10%] w-64 h-64 bg-primary/5 blur-[80px] rounded-full group-hover:bg-primary/10 transition-all duration-500" />
                    </motion.div>

                    {/* For Companies */}
                    <motion.div
                        className="group relative p-12 bg-zinc-900 border border-zinc-800 rounded-[48px] overflow-hidden hover:shadow-2xl transition-all duration-500"
                        initial={{ opacity: 0, x: 50 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                    >
                        <div className="relative z-10">
                            <div className="w-16 h-16 bg-secondary/20 text-secondary rounded-3xl flex items-center justify-center mb-8 group-hover:scale-110 transition-transform">
                                <Building2 className="w-8 h-8" />
                            </div>
                            <h3 className="text-4xl font-black font-display text-white mb-4 italic">For Companies</h3>
                            <p className="text-lg text-gray-400 mb-8 max-w-md">
                                Hire 10x faster with AI-pre-screened candidates. High accuracy matching with automated pipelines.
                            </p>
                            <ul className="space-y-4 mb-10">
                                {["Sub-second Batch Screening", "Custom Evaluation Weights", "Collaboration Dashboard"].map((item) => (
                                    <li key={item} className="flex items-center space-x-3 text-sm font-bold text-gray-300">
                                        <Target className="w-4 h-4 text-secondary" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <Link
                                href="/register?role=recruiter"
                                className="inline-flex items-center space-x-3 px-8 py-4 bg-secondary text-zinc-900 rounded-2xl font-black shadow-xl shadow-secondary/30 hover:scale-[1.05] active:scale-[0.98] transition-all"
                            >
                                <span>Post a Job</span>
                                <ChevronRight className="w-5 h-5 group-hover:translate-x-1" />
                            </Link>
                        </div>
                        {/* Abstract background shape */}
                        <div className="absolute top-1/2 right-[-10%] w-64 h-64 bg-secondary/5 blur-[80px] rounded-full group-hover:bg-secondary/10 transition-all duration-500" />
                    </motion.div>
                </div>
            </div>
        </section>
    );
};

export default RoleSelection;
