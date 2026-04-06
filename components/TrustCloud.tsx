"use client";

import { motion } from "framer-motion";
import { Chrome, Figma, Github, Slack, Database, Cpu } from "lucide-react";

const logos = [
    { name: "Google", icon: <Chrome className="w-5 h-5" /> },
    { name: "Figma", icon: <Figma className="w-5 h-5" /> },
    { name: "GitHub", icon: <Github className="w-5 h-5" /> },
    { name: "Slack", icon: <Slack className="w-5 h-5" /> },
    { name: "Supabase", icon: <Database className="w-5 h-5 text-emerald-500" /> },
    { name: "Mistral AI", icon: <Cpu className="w-5 h-5 text-orange-500" /> },
];

const TrustCloud = () => {
    return (
        <section className="py-24 bg-white/50 backdrop-blur-sm border-y border-gray-100 overflow-hidden">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="text-center mb-12">
                    <p className="text-xs font-black uppercase tracking-[0.3em] text-gray-400">
                        Trusted by High-Velocity Teams Worldwide
                    </p>
                </div>
                
                <div className="relative flex overflow-hidden group">
                    <motion.div
                        className="flex space-x-12 whitespace-nowrap py-4"
                        animate={{ x: [0, -1000] }}
                        transition={{
                            repeat: Infinity,
                            duration: 30,
                            ease: "linear",
                        }}
                    >
                        {[...logos, ...logos, ...logos].map((logo, i) => (
                            <div
                                key={i}
                                className="flex items-center space-x-3 grayscale hover:grayscale-0 transition-all duration-500 opacity-40 hover:opacity-100 cursor-default"
                            >
                                <div className="p-2 bg-gray-50 border border-gray-100 rounded-lg">
                                    {logo.icon}
                                </div>
                                <span className="text-xl font-bold font-display text-gray-800 uppercase tracking-tighter">
                                    {logo.name}
                                </span>
                            </div>
                        ))}
                    </motion.div>
                </div>
            </div>
            
            {/* Gradient Mask */}
            <div className="absolute inset-y-0 left-0 w-32 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
            <div className="absolute inset-y-0 right-0 w-32 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />
        </section>
    );
};

export default TrustCloud;
