"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus, HelpCircle } from "lucide-react";

const faqs = [
    {
        q: "How does the AI ranking work?",
        a: "Our engine uses a multi-layered approach: identifying skills through Named Entity Recognition (NER), calculating semantic similarity with vector embeddings, and scoring work experience depth vs role requirements. Powered by Groq™, this happens in milliseconds."
    },
    {
        q: "Is candidate data secure?",
        a: "Yes. HireSight is built on Supabase with strict Row Level Security (RLS). Personal data is encrypted at rest, and we are fully GDPR/CCPA compliant. You control who sees your data at all times."
    },
    {
        q: "Can I use HireSight with my existing ATS?",
        a: "Absolutely. We offer bulk CSV/Excel exports and a dedicated API for Pro/Enterprise users to push ranked candidates directly into systems like Greenhouse, Lever, or Workday."
    },
    {
        q: "How do you mitigate bias?",
        a: "By default, our AI screener 'blind-matches' based on objective criteria—skills, experience, and certifications. Identity markers like name, gender, and age are excluded from the initial ranking algorithm."
    },
    {
        q: "What AI models are you using?",
        a: "We leverage a hybrid stack of Mistral 7B for detailed parsing and custom Llama-3 models via Groq for high-speed batch inference, ensuring both accuracy and sub-second performance."
    }
];

const FAQ = () => {
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    return (
        <section className="py-32 bg-white relative">
            <div className="max-w-4xl mx-auto px-6 lg:px-8">
                <div className="text-center mb-16">
                    <div className="inline-flex items-center space-x-2 px-3 py-1 bg-gray-100 rounded-full mb-4">
                        <HelpCircle className="w-4 h-4 text-gray-400" />
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Support</span>
                    </div>
                    <h2 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tight">
                        Common <span className="text-primary tracking-normal">Questions</span>
                    </h2>
                </div>

                <div className="space-y-4">
                    {faqs.map((faq, i) => (
                        <div 
                            key={i}
                            className={`border-2 rounded-[32px] transition-all duration-300 overflow-hidden ${
                                openIndex === i ? "border-primary/20 bg-primary/[0.02]" : "border-gray-50 bg-white"
                            }`}
                        >
                            <button
                                onClick={() => setOpenIndex(openIndex === i ? null : i)}
                                className="w-full px-8 py-7 flex items-center justify-between text-left group"
                            >
                                <span className="text-xl font-black text-zinc-900 italic tracking-tight group-hover:text-primary transition-colors">
                                    {faq.q}
                                </span>
                                <div className={`p-2 rounded-full transition-all ${
                                    openIndex === i ? "bg-primary text-white rotate-180" : "bg-gray-100 text-gray-400"
                                }`}>
                                    {openIndex === i ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                                </div>
                            </button>
                            
                            <AnimatePresence>
                                {openIndex === i && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        transition={{ duration: 0.3, ease: "easeOut" }}
                                    >
                                        <div className="px-8 pb-8 text-lg text-gray-500 leading-relaxed max-w-3xl">
                                            {faq.a}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default FAQ;
