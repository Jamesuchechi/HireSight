"use client";

import { motion } from "framer-motion";
import { Check, X, TrendingUp, Clock, Target, Scale } from "lucide-react";

const comparisonData = [
    { feature: "Resume Screening", manual: "2-4 hours per batch", ai: "Sub-seconds", icon: <Clock className="w-5 h-5 text-gray-400" /> },
    { feature: "Candidate Matching", manual: "Keyword-based", ai: "Deep Semantic Context", icon: <Target className="w-5 h-5 text-gray-400" /> },
    { feature: "Bias Mitigation", manual: "Manual Anonymization", ai: "Native Identity Blind", icon: <Scale className="w-5 h-5 text-gray-400" /> },
    { feature: "Performance Search", manual: "Limited Sorting", ai: "Global Rank Analytics", icon: <TrendingUp className="w-5 h-5 text-gray-400" /> },
];

const ComparisonSection = () => {
    return (
        <section className="py-32 bg-gray-50 relative">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="text-center mb-20">
                    <h2 className="text-4xl md:text-6xl font-black font-display text-zinc-900 mb-6 tracking-tight">
                        Why Choose <span className="text-primary italic">HireSight?</span>
                    </h2>
                    <p className="max-w-2xl mx-auto text-xl text-gray-500">
                        Traditional hiring is slow and biased. We built the engine that replaces the bottleneck.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    {/* Visual Comparison Table */}
                    <motion.div
                        className="bg-white rounded-[40px] border border-gray-100 shadow-2xl overflow-hidden"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-gray-50">
                                    <th className="p-8 text-xs font-black uppercase tracking-widest text-gray-400">Features</th>
                                    <th className="p-8 text-xs font-black uppercase tracking-widest text-gray-400">Manual</th>
                                    <th className="p-8 text-xs font-black uppercase tracking-widest text-primary">HireSight AI</th>
                                </tr>
                            </thead>
                            <tbody>
                                {comparisonData.map((row, i) => (
                                    <motion.tr
                                        key={row.feature}
                                        className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
                                        initial={{ opacity: 0, x: -20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        transition={{ delay: i * 0.1 }}
                                        viewport={{ once: true }}
                                    >
                                        <td className="p-8">
                                            <div className="flex items-center space-x-3">
                                                {row.icon}
                                                <span className="font-bold text-zinc-800">{row.feature}</span>
                                            </div>
                                        </td>
                                        <td className="p-8">
                                            <div className="flex items-center space-x-2 text-gray-400 font-medium">
                                                <X className="w-4 h-4 text-red-400" />
                                                <span>{row.manual}</span>
                                            </div>
                                        </td>
                                        <td className="p-8">
                                            <div className="flex items-center space-x-2 text-primary font-black italic">
                                                <Check className="w-5 h-5 text-emerald-500" />
                                                <span>{row.ai}</span>
                                            </div>
                                        </td>
                                    </motion.tr>
                                ))}
                            </tbody>
                        </table>
                    </motion.div>

                    {/* Stats/Metrics context */}
                    <div className="space-y-8">
                        <div className="p-8 bg-zinc-900 rounded-[32px] text-white">
                            <h4 className="text-4xl font-black font-display mb-2 italic">98%</h4>
                            <p className="text-gray-400 font-bold uppercase tracking-widest text-xs mb-4">Time Efficiency Improvement</p>
                            <p className="text-gray-300">
                                Companies using HireSight report an average reduction in screening hours from days to literal seconds.
                            </p>
                        </div>
                        <div className="p-8 bg-primary text-white rounded-[32px]">
                            <h4 className="text-4xl font-black font-display mb-2 italic">0%</h4>
                            <p className="text-primary-foreground/60 font-bold uppercase tracking-widest text-xs mb-4">Implicit Human Bias</p>
                            <p className="text-white/90">
                                Our AI logic ignores identity demographics by default, focusing solely on skill-to-role matching.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default ComparisonSection;
