"use client";

import { motion } from "framer-motion";
import { Star, Quote, UserCircle } from "lucide-react";

const reviews = [
    {
        name: "Alex Rivera",
        role: "Head of Talent, TechFlow",
        text: "HireSight transformed our hiring. We screened 200 applicants for a Senior Eng role in seconds. The match accuracy is frighteningly good.",
        avatar: "AR"
    },
    {
        name: "Lila Nguyen",
        role: "Startup Founder, Prism",
        text: "As a solo founder, HireSight is my secret weapon. It finding the diamonds in the rough without me spending hours reading PDFs.",
        avatar: "LN"
    },
    {
        name: "James Wilson",
        role: "Recruitment Lead, GlobalScale",
        text: "Bias-free screening is no longer a corporate promise, it's a reality with HireSight. Highly recommended for any serious recruiter.",
        avatar: "JW"
    }
];

const Testimonials = () => {
    return (
        <section className="py-32 bg-white relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="text-center mb-16">
                    <Quote className="w-12 h-12 text-primary mx-auto mb-6 opacity-20" />
                    <h2 className="text-4xl md:text-6xl font-black font-display text-zinc-900 mb-6 italic tracking-tight">
                        Loved by the World's <br />
                        <span className="text-primary tracking-normal">Best Teams</span>
                    </h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    {reviews.map((r, i) => (
                        <motion.div
                            key={r.name}
                            className="p-8 bg-gray-50 border border-gray-100 rounded-[40px] hover:shadow-2xl hover:scale-[1.02] transition-all duration-500 relative group"
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            transition={{ delay: i * 0.1 }}
                            viewport={{ once: true }}
                        >
                            <div className="flex space-x-1 mb-6 text-accent">
                                {[...Array(5)].map((_, i) => <Star key={i} className="w-4 h-4 fill-current" />)}
                            </div>
                            <p className="text-lg text-gray-600 mb-8 font-medium italic leading-relaxed">
                                "{r.text}"
                            </p>
                            <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 bg-zinc-900 text-white rounded-full flex items-center justify-center font-bold">
                                    {r.avatar}
                                </div>
                                <div>
                                    <h4 className="text-zinc-900 font-black">{r.name}</h4>
                                    <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">{r.role}</p>
                                </div>
                            </div>
                            {/* Decorative element */}
                            <div className="absolute top-[-10%] right-[-10%] w-32 h-32 bg-primary/5 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default Testimonials;
