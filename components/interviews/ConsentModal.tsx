"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, BrainCircuit, Video, Lock, Check, X } from "lucide-react";

interface ConsentModalProps {
    isOpen: boolean;
    onAccept: () => void;
    onDecline: () => void;
}

export default function ConsentModal({ isOpen, onAccept, onDecline }: ConsentModalProps) {
    const [agreed, setAgreed] = useState(false);

    return (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 bg-black/90 backdrop-blur-xl"
                    />
                    
                    <motion.div 
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="relative w-full max-w-xl bg-zinc-900 border border-white/10 rounded-[48px] shadow-2xl overflow-hidden"
                    >
                        <div className="p-12 space-y-10">
                            {/* Header */}
                            <div className="text-center space-y-4">
                                <div className="w-20 h-20 bg-primary/10 rounded-[32px] flex items-center justify-center mx-auto border border-primary/20">
                                    <ShieldCheck className="w-10 h-10 text-primary" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-3xl font-black text-white italic tracking-tighter uppercase">Mission Authorization</h3>
                                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest leading-none">AI Intelligence & Privacy Protocol</p>
                                </div>
                            </div>

                            {/* Terms */}
                            <div className="space-y-6">
                                <ProtocolItem 
                                    icon={<BrainCircuit className="w-5 h-5" />}
                                    title="AI Synthesis"
                                    description="Your responses and interactions will be analyzed by AI to generate performance metrics and objective feedback."
                                />
                                <ProtocolItem 
                                    icon={<Video className="w-5 h-5" />}
                                    title="Biometric Sync"
                                    description="Video and audio streams are processed in real-time for transcription and communication synchronization."
                                />
                                <ProtocolItem 
                                    icon={<Lock className="w-5 h-5" />}
                                    title="Data Encapsulation"
                                    description="All personal data is encrypted and accessible only to the authorized hiring squadron for this protocol."
                                />
                            </div>

                            {/* Checkbox */}
                            <label className="flex items-start space-x-4 cursor-pointer group p-6 bg-white/5 rounded-3xl border border-white/5 hover:border-primary/20 transition-all">
                                <input 
                                    type="checkbox" 
                                    checked={agreed}
                                    onChange={(e) => setAgreed(e.target.checked)}
                                    className="mt-1 w-5 h-5 rounded-md border-white/10 bg-black text-primary focus:ring-primary/20"
                                />
                                <span className="text-xs font-bold text-gray-400 italic leading-relaxed group-hover:text-white transition-colors">
                                    I acknowledge the AI assessment protocols and authorize the secure processing of my biometric and technical data.
                                </span>
                            </label>

                            {/* Actions */}
                            <div className="grid grid-cols-2 gap-4 pt-4">
                                <button 
                                    onClick={onDecline}
                                    className="py-5 border border-white/10 text-gray-400 rounded-3xl font-black text-[10px] uppercase tracking-widest italic hover:bg-white/5 transition-all"
                                >
                                    Abort Mission
                                </button>
                                <button 
                                    onClick={onAccept}
                                    disabled={!agreed}
                                    className={`py-5 rounded-3xl font-black text-[10px] uppercase tracking-widest italic transition-all flex items-center justify-center space-x-2 ${
                                        agreed ? 'bg-primary text-white shadow-xl shadow-primary/20 hover:scale-105' : 'bg-zinc-800 text-gray-600 cursor-not-allowed'
                                    }`}
                                >
                                    <Check className="w-4 h-4" />
                                    <span>Authorize Access</span>
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}

function ProtocolItem({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
    return (
        <div className="flex items-start space-x-4">
            <div className="p-3 bg-white/5 rounded-2xl text-primary shrink-0 border border-white/5">
                {icon}
            </div>
            <div className="space-y-1">
                <h4 className="text-[10px] font-black text-white uppercase tracking-widest italic">{title}</h4>
                <p className="text-xs text-gray-500 font-bold italic leading-tight">{description}</p>
            </div>
        </div>
    );
}
