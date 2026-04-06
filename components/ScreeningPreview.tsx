"use client";

import { motion } from "framer-motion";
import { CheckCircle2, AlertCircle, TrendingUp, Cpu, Timer, ShieldCheck } from "lucide-react";

interface CandidateCardProps {
    name: string;
    score: number;
    skills: string[];
    role: string;
    delay: number;
}

const CandidateCard = ({ name, score, skills, role, delay }: CandidateCardProps) => (
    <motion.div
        initial={{ opacity: 0, x: -20 }}
        whileInView={{ opacity: 1, x: 0 }}
        viewport={{ once: true }}
        transition={{ delay, duration: 0.5 }}
        className="p-6 bg-white border border-gray-100 rounded-3xl shadow-sm hover:shadow-xl hover:scale-[1.02] transition-all duration-300"
    >
        <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-zinc-400 font-bold">
                    {name[0]}
                </div>
                <div>
                    <h4 className="text-lg font-black text-zinc-900">{name}</h4>
                    <p className="text-sm text-gray-500">{role}</p>
                </div>
            </div>
            <div className="text-right">
                <div className="text-2xl font-black text-primary italic leading-none">{score}%</div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1">Match Score</p>
            </div>
        </div>
        
        <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
                <span key={s} className="px-3 py-1 bg-gray-50 border border-gray-100 text-[10px] font-bold text-gray-600 rounded-lg uppercase tracking-wider">
                    {s}
                </span>
            ))}
        </div>
    </motion.div>
);

const ScreeningPreview = () => {
    return (
        <section id="how-it-works" className="py-32 bg-gray-50 relative overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-[0.02]" style={{ backgroundImage: 'radial-gradient(circle at 10px 10px, #000 1px, transparent 0)', backgroundSize: '24px 24px' }} />

            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                    {/* Left side: Context */}
                    <div>
                        <div className="inline-flex items-center space-x-2 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full mb-6">
                            <Cpu className="w-4 h-4 text-primary" />
                            <span className="text-xs font-bold text-primary uppercase tracking-widest">Groq™ Powered Inference</span>
                        </div>
                        <h2 className="text-5xl md:text-6xl font-black font-display text-zinc-900 leading-tight mb-8">
                            Screen 50+ Resumes <br />
                            <span className="text-secondary">In Under <span className="italic">1 Second</span></span>
                        </h2>
                        <div className="space-y-6">
                            {[
                                { icon: <Timer className="w-6 h-6 text-primary" />, title: "Instant Analysis", desc: "No more waiting for hours. Our AI processes resumes the moment they arrive." },
                                { icon: <TrendingUp className="w-6 h-6 text-secondary" />, title: "Contextual Scoring", desc: "We evaluate experience longevity, skill relevance, and cultural indicators." },
                                { icon: <ShieldCheck className="w-6 h-6 text-accent" />, title: "Bias-Free Evaluation", desc: "Our engine is trained to focus on merit, excluding identifying demographics." }
                            ].map((item, i) => (
                                <motion.div 
                                    key={i} 
                                    className="flex space-x-4"
                                    initial={{ opacity: 0, x: -20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: i * 0.1 }}
                                >
                                    <div className="flex-shrink-0 w-12 h-12 bg-white rounded-2xl border border-gray-100 shadow-sm flex items-center justify-center">
                                        {item.icon}
                                    </div>
                                    <div>
                                        <h4 className="text-xl font-bold text-zinc-900 mb-1">{item.title}</h4>
                                        <p className="text-gray-500 leading-relaxed">{item.desc}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </div>

                    {/* Right side: Mock-up UI */}
                    <div className="relative">
                        <div className="absolute inset-0 bg-primary/20 blur-[100px] animate-pulse -z-10" />
                        <div className="p-8 bg-white/40 backdrop-blur-3xl border border-white/50 rounded-[48px] shadow-2xl relative overflow-hidden">
                            {/* Glass overlay */}
                            <div className="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent pointer-events-none" />
                            
                            <div className="relative space-y-6">
                                <div className="flex items-center justify-between mb-8">
                                    <h3 className="text-2xl font-black font-display text-zinc-900">Ranked Results</h3>
                                    <div className="px-4 py-2 bg-zinc-900 text-white rounded-2xl text-xs font-bold tracking-widest uppercase">
                                        Processing Complete
                                    </div>
                                </div>
                                
                                <CandidateCard 
                                    name="Sarah Chen" 
                                    score={98} 
                                    role="Senior Software Engineer" 
                                    skills={["React", "Next.js", "PostgreSQL", "Node.js"]} 
                                    delay={0.2}
                                />
                                <CandidateCard 
                                    name="Marcus Miller" 
                                    score={94} 
                                    role="Fullstack Developer" 
                                    skills={["Next.js", "Lucia Auth", "Cloudflare", "Tailwind"]} 
                                    delay={0.4}
                                />
                                <CandidateCard 
                                    name="Elena Rodriguez" 
                                    score={89} 
                                    role="Frontend Specialist" 
                                    skills={["React", "Framer Motion", "Typescript"]} 
                                    delay={0.6}
                                />

                                {/* Interactive element */}
                                <div className="pt-8 border-t border-gray-100 flex items-center justify-center">
                                    <button className="flex items-center space-x-3 px-8 py-4 bg-zinc-900 text-white rounded-2xl font-black italic hover:scale-105 transition-transform shadow-xl">
                                        <span>Full Screening Report</span>
                                        <TrendingUp className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default ScreeningPreview;
