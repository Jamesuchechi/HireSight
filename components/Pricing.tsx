"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Rocket, Zap, Crown } from "lucide-react";

const seekerPlans = [
    { name: "Free Seeker", price: "0", features: ["1 Primary Resume", "5 Job Applications/mo", "Basic Match Score", "Email Alerts"], icon: <Rocket className="w-5 h-5" />, cta: "Get Started" },
    { name: "Pro Seeker", price: "12", features: ["Unlimited Resumes", "Infinite Applications", "Deep AI Skill Analysis", "AI Optimizer Tips", "Priority Recommendations"], icon: <Crown className="w-5 h-5 text-accent" />, cta: "Start Free Trial", popular: true },
];

const recruiterPlans = [
    { name: "Basic Recruiter", price: "0", features: ["1 Active Job Post", "50 Screenings/mo", "Basic Ranking", "Team Invites"], icon: <Zap className="w-5 h-5" />, cta: "Try Now" },
    { name: "Scale Recruiter", price: "49", features: ["Unlimited Job Posts", "Infinite AI Screening", "Custom Weights Engine", "ATS Export", "Dashboard Analytics"], icon: <Crown className="w-5 h-5 text-accent" />, cta: "Go Pro", popular: true },
];

const Pricing = () => {
    const [role, setRole] = useState<"seeker" | "recruiter">("seeker");

    return (
        <section id="pricing" className="py-32 bg-gray-50 relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-6 lg:px-8 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-6xl font-black font-display text-zinc-900 mb-6 italic tracking-tight">
                        Simple, Transparent <br />
                        <span className="text-primary tracking-normal">Pricing</span>
                    </h2>
                    
                    {/* Toggle Switch */}
                    <div className="flex items-center justify-center space-x-4">
                        <span className={`text-sm font-bold ${role === "seeker" ? "text-primary" : "text-gray-400"}`}>Job Seeker</span>
                        <button 
                            onClick={() => setRole(role === "seeker" ? "recruiter" : "seeker")}
                            className="w-16 h-8 bg-gray-200 rounded-full relative p-1 transition-colors hover:bg-gray-300"
                        >
                            <motion.div 
                                className="w-6 h-6 bg-white rounded-full shadow-sm"
                                animate={{ x: role === "seeker" ? 0 : 32 }}
                            />
                        </button>
                        <span className={`text-sm font-bold ${role === "recruiter" ? "text-primary" : "text-gray-400"}`}>Recruiter</span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                    <AnimatePresence mode="wait">
                        {(role === "seeker" ? seekerPlans : recruiterPlans).map((plan, i) => (
                            <motion.div
                                key={plan.name}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ delay: i * 0.1 }}
                                className={`relative p-8 rounded-[40px] border-2 flex flex-col justify-between group overflow-hidden ${
                                    plan.popular ? "bg-zinc-900 border-zinc-900 text-white shadow-2xl scale-[1.05]" : "bg-white border-gray-100"
                                } shadow-xl transition-all duration-500`}
                            >
                                {plan.popular && (
                                    <div className="absolute top-6 right-6 px-4 py-1 bg-primary text-white text-[10px] font-black uppercase tracking-widest rounded-full">
                                        Most Popular
                                    </div>
                                )}
                                <div>
                                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-6 ${plan.popular ? 'bg-white/10 text-white' : 'bg-primary/10 text-primary'}`}>
                                        {plan.icon}
                                    </div>
                                    <h3 className="text-2xl font-black font-display mb-2 italic">{plan.name}</h3>
                                    <div className="flex items-baseline space-x-1 mb-8">
                                        <span className="text-4xl font-black font-display">${plan.price}</span>
                                        <span className={`text-sm font-bold ${plan.popular ? 'text-gray-400' : 'text-gray-500'}`}>/month</span>
                                    </div>
                                    <ul className="space-y-4 mb-12">
                                        {plan.features.map((f) => (
                                            <li key={f} className="flex items-center space-x-3 text-sm font-bold">
                                                <Check className={`w-4 h-4 flex-shrink-0 ${plan.popular ? 'text-primary' : 'text-emerald-500'}`} />
                                                <span className={plan.popular ? 'text-gray-300' : 'text-gray-600'}>{f}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <button className={`w-full py-4 rounded-2xl font-black text-sm transition-all hover:scale-105 active:scale-[0.98] ${
                                    plan.popular ? "bg-primary text-white shadow-xl shadow-primary/30" : "bg-gray-100 text-zinc-900 hover:bg-gray-200"
                                }`}>
                                    {plan.cta}
                                </button>

                                {/* Decorative shape for popular card */}
                                {plan.popular && (
                                    <div className="absolute bottom-[-10%] left-[-10%] w-32 h-32 bg-primary/20 blur-3xl rounded-full pointer-events-none" />
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </div>
            
            {/* Background elements */}
            <div className="absolute top-1/4 left-[-10%] w-96 h-96 bg-primary/5 blur-[120px] rounded-full -z-10" />
            <div className="absolute bottom-1/4 right-[-10%] w-80 h-80 bg-secondary/10 blur-[100px] rounded-full -z-10" />
        </section>
    );
};

export default Pricing;
