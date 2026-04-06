"use client";

import { motion } from "framer-motion";
import { BrainCircuit, Fingerprint, Zap, Layers, BarChart3, MessageSquare } from "lucide-react";

const features = [
    {
        title: "Semantic AI Matching",
        desc: "Our models understand context, synonyms, and experience quality, not just keywords.",
        icon: <BrainCircuit className="w-8 h-8" />,
        className: "md:col-span-2 md:row-span-2 bg-primary/5 border-primary/20",
        color: "text-primary"
    },
    {
        title: "Bias-Free Screening",
        desc: "Identity-blind matching ensures the best talent wins based on merit.",
        icon: <Fingerprint className="w-8 h-8" />,
        className: "md:col-span-1 md:row-span-1 bg-secondary/5 border-secondary/20",
        color: "text-secondary"
    },
    {
        title: "Instant Results",
        desc: "Groq™ LPU powered inference processes 50+ resumes in sub-seconds.",
        icon: <Zap className="w-8 h-8" />,
        className: "md:col-span-1 md:row-span-1 bg-accent/5 border-accent/20",
        color: "text-accent"
    },
    {
        title: "Visual Pipeline",
        desc: "Kanban board for seamless candidate management from offer to hire.",
        icon: <Layers className="w-6 h-6" />,
        className: "md:col-span-1 md:row-span-1 bg-zinc-900 border-zinc-700 text-white",
        color: "text-white"
    },
    {
        title: "Deep Analytics",
        desc: "Track time-to-hire and skill gap metrics with actionable insights.",
        icon: <BarChart3 className="w-6 h-6" />,
        className: "md:col-span-2 md:row-span-1 bg-gray-50 border-gray-200",
        color: "text-gray-900"
    }
];

const FeatureGrid = () => {
    return (
        <section id="features" className="py-32 bg-white relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                {/* Header */}
                <div className="text-center mb-20">
                    <motion.h2 
                        className="text-4xl md:text-6xl font-black font-display text-zinc-900 mb-6"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        Built for <span className="text-primary italic">High-Velocity</span> Hiring
                    </motion.h2>
                    <p className="max-w-2xl mx-auto text-xl text-gray-500">
                        HireSight 2.0 combines enterprise-grade AI with a premium user experience to help you close candidates faster.
                    </p>
                </div>

                {/* Bento Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[240px]">
                    {features.map((f, i) => (
                        <motion.div
                            key={f.title}
                            className={`relative p-8 rounded-[32px] border-2 flex flex-col justify-between group overflow-hidden ${f.className}`}
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            whileHover={{ y: -8 }}
                            transition={{ delay: i * 0.1, duration: 0.5 }}
                            viewport={{ once: true }}
                        >
                            <div className="relative z-10">
                                <div className={`mb-6 ${f.color} transform group-hover:scale-110 transition-transform duration-500`}>
                                    {f.icon}
                                </div>
                                <h3 className={`text-2xl font-black font-display mb-4 ${f.className.includes('zinc-900') ? 'text-white' : 'text-zinc-900'}`}>
                                    {f.title}
                                </h3>
                                <p className={`text-lg leading-relaxed ${f.className.includes('zinc-900') ? 'text-gray-400' : 'text-gray-500'}`}>
                                    {f.desc}
                                </p>
                            </div>
                            
                            {/* Decorative element */}
                            <div className="absolute top-[-20%] right-[-20%] w-40 h-40 bg-white/10 blur-3xl rounded-full group-hover:bg-white/20 transition-all duration-700" />
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default FeatureGrid;
