"use client";

import { Layout, Type, Laptop, Check, Zap, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

interface TemplateSwitcherProps {
    current: 'modern' | 'classic' | 'minimal' | 'executive' | 'creative' | 'technical';
    onSelect: (theme: 'modern' | 'classic' | 'minimal' | 'executive' | 'creative' | 'technical') => void;
}

const templates = [
    { id: 'modern', label: 'Modern', icon: <Laptop className="w-4 h-4" />, description: 'Clean & Visual' },
    { id: 'executive', label: 'Executive', icon: <Zap className="w-4 h-4 text-amber-500" />, description: 'Strategic & Powerful' },
    { id: 'creative', label: 'Creative', icon: <Sparkles className="w-4 h-4 text-purple-500" />, description: 'Bold & Narrative' },
    { id: 'technical', label: 'Technical', icon: <Type className="w-4 h-4 text-emerald-500" />, description: 'Precise & Structured' },
    { id: 'classic', label: 'Classic', icon: <Type className="w-4 h-4" />, description: 'High-Density Corporate' },
    { id: 'minimal', label: 'Minimal', icon: <Layout className="w-4 h-4" />, description: 'Clean White Space' },
];

export default function TemplateSwitcher({ current, onSelect }: TemplateSwitcherProps) {
    return (
        <div className="bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm">
            <h3 className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-6 ml-2">Visual Persona</h3>
            <div className="space-y-3">
                {templates.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => onSelect(t.id as any)}
                        className={`w-full text-left p-4 rounded-2xl transition-all border-2 flex items-center justify-between group ${
                            current === t.id 
                            ? "border-primary bg-primary/5 text-zinc-900" 
                            : "border-transparent bg-gray-50 text-gray-400 hover:bg-gray-100"
                        }`}
                    >
                        <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-lg transition-colors ${
                                current === t.id ? "bg-primary text-white" : "bg-white text-gray-400 group-hover:text-zinc-900"
                            }`}>
                                {t.icon}
                            </div>
                            <div>
                                <p className="text-[10px] font-black uppercase tracking-widest leading-none mb-1">{t.label}</p>
                                <p className="text-[9px] font-bold text-gray-400 uppercase tracking-tighter leading-none">{t.description}</p>
                            </div>
                        </div>
                        {current === t.id && (
                            <div className="w-5 h-5 bg-primary text-white rounded-full flex items-center justify-center scale-110">
                                <Check className="w-3 h-3" />
                            </div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
}
