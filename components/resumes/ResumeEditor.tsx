"use client";

import { useState } from "react";
import { 
    User, 
    Mail, 
    Phone, 
    MapPin, 
    Link as LinkIcon, 
    Briefcase, 
    GraduationCap, 
    Plus, 
    Trash2,
    Save,
    Sparkles,
    Loader2
} from "lucide-react";
import { motion } from "framer-motion";

interface SectionProps {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    onAdd?: () => void;
}

const Section = ({ title, icon, children, onAdd }: SectionProps) => (
    <div className="bg-white border border-gray-100 rounded-[32px] p-8 shadow-sm hover:shadow-md transition-all mb-8">
        <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
                <div className="p-3 bg-zinc-900 text-white rounded-2xl">
                    {icon}
                </div>
                <h3 className="text-xl font-black font-display text-zinc-900 italic uppercase tracking-tight">{title}</h3>
            </div>
            {onAdd && (
                <button 
                    onClick={onAdd}
                    className="p-2 hover:bg-gray-50 rounded-full transition-colors"
                >
                    <Plus className="w-5 h-5 text-gray-400 hover:text-zinc-900" />
                </button>
            )}
        </div>
        {children}
    </div>
);

export default function ResumeEditor({ initialData, onSave, onAICall }: { 
    initialData: any;
    onSave: (data: any) => void;
    onAICall?: (section: string, content: any) => Promise<string>;
}) {
    const [data, setData] = useState(initialData);
    const [aiLoading, setAiLoading] = useState<string | null>(null);

    const handleInlineAI = async (path: string, content: any) => {
        if (!onAICall) return;
        setAiLoading(path);
        try {
            const improved = await onAICall(path, content);
            if (improved) {
                updateNested(path, improved);
            }
        } finally {
            setAiLoading(null);
        }
    };

    const updateNested = (path: string, value: any) => {
        const keys = path.split('.');
        const newData = { ...data };
        let current = newData;
        for (let i = 0; i < keys.length - 1; i++) {
            current = current[keys[i]];
        }
        current[keys[keys.length - 1]] = value;
        setData(newData);
    };

    return (
        <div className="space-y-4">
            {/* Contact Info */}
            <Section title="Basic Identity" icon={<User className="w-5 h-5" />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-1">Full Name</label>
                        <input 
                            value={data.fullName}
                            onChange={(e) => setData({ ...data, fullName: e.target.value })}
                            className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-zinc-900 focus:ring-2 focus:ring-primary/20 outline-none"
                        />
                    </div>
                    <div className="space-y-2 text-gray-400">
                         <label className="text-[10px] font-black uppercase tracking-widest ml-1">Email Protocol</label>
                         <div className="relative">
                            <Mail className="absolute left-6 top-1/2 -translate-y-1/2 w-4 h-4" />
                            <input 
                                value={data.contact?.email}
                                onChange={(e) => updateNested('contact.email', e.target.value)}
                                className="w-full bg-gray-50 border-none rounded-2xl pl-14 pr-6 py-4 font-bold text-zinc-900 focus:ring-2 focus:ring-primary/20 outline-none"
                            />
                         </div>
                    </div>
                </div>
            </Section>

            {/* Professional Summary */}
            <Section title="The Synopsis" icon={<Sparkles className="w-5 h-5" />}>
                <div className="space-y-2 relative group/field">
                    <div className="flex items-center justify-between">
                        <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-1">AI Generated Summary</label>
                        <button 
                            onClick={() => handleInlineAI('summary', data.summary)}
                            disabled={!!aiLoading}
                            className="p-1.5 opacity-0 group-hover/field:opacity-100 transition-all hover:bg-primary/10 rounded-lg text-primary"
                            title="AI Rewrite"
                        >
                            {aiLoading === 'summary' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                        </button>
                    </div>
                    <textarea 
                        value={data.summary}
                        onChange={(e) => setData({ ...data, summary: e.target.value })}
                        rows={4}
                        className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-medium text-zinc-600 leading-relaxed focus:ring-2 focus:ring-primary/20 outline-none resize-none"
                    />
                </div>
            </Section>

            {/* Experience */}
            <Section title="Operational History" icon={<Briefcase className="w-5 h-5" />} onAdd={() => {}}>
                <div className="space-y-8">
                    {data.experience?.map((exp: any, idx: number) => (
                        <div key={idx} className="relative pl-8 border-l-2 border-gray-100 group">
                            <div className="absolute left-[-9px] top-0 w-4 h-4 bg-white border-2 border-primary rounded-full group-hover:scale-125 transition-transform" />
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <input 
                                    value={exp.company}
                                    onChange={(e) => {
                                        const newExp = [...data.experience];
                                        newExp[idx].company = e.target.value;
                                        setData({ ...data, experience: newExp });
                                    }}
                                    placeholder="Entity Name"
                                    className="bg-transparent border-none p-0 text-lg font-black font-display italic uppercase tracking-tight text-zinc-900 focus:ring-0 outline-none"
                                />
                                <input 
                                    value={exp.duration}
                                    onChange={(e) => {
                                        const newExp = [...data.experience];
                                        newExp[idx].duration = e.target.value;
                                        setData({ ...data, experience: newExp });
                                    }}
                                    placeholder="Cycle (e.g. 2020 - Present)"
                                    className="bg-transparent border-none p-0 text-xs font-black uppercase tracking-widest text-primary md:text-right focus:ring-0 outline-none"
                                />
                            </div>
                            <input 
                                value={exp.role}
                                onChange={(e) => {
                                    const newExp = [...data.experience];
                                    newExp[idx].role = e.target.value;
                                    setData({ ...data, experience: newExp });
                                }}
                                placeholder="Operating Role"
                                className="w-full bg-transparent border-none p-0 text-sm font-bold text-gray-500 uppercase tracking-widest mb-4 focus:ring-0 outline-none"
                            />
                            <div className="space-y-3">
                                {exp.highlights?.map((h: string, hIdx: number) => (
                                    <div key={hIdx} className="flex group/item py-1">
                                        <div className="mt-1.5 w-1.5 h-1.5 bg-gray-200 rounded-full mr-4 flex-shrink-0" />
                                        <div className="flex-grow flex items-start space-x-3 group/field">
                                            <textarea 
                                                value={h}
                                                rows={1}
                                                className="flex-grow bg-transparent border-none p-0 text-sm font-medium text-gray-500 leading-relaxed focus:ring-0 outline-none resize-none h-auto overflow-hidden"
                                                onChange={(e) => {
                                                    const newExp = [...data.experience];
                                                    newExp[idx].highlights[hIdx] = e.target.value;
                                                    setData({ ...data, experience: newExp });
                                                }}
                                            />
                                            <button 
                                                onClick={() => handleInlineAI(`experience.${idx}.highlights.${hIdx}`, h)}
                                                disabled={!!aiLoading}
                                                className="opacity-0 group-hover/field:opacity-100 p-1 hover:bg-primary/5 rounded transition-all text-primary"
                                                title="AI Optimize"
                                            >
                                                {aiLoading === `experience.${idx}.highlights.${hIdx}` ? (
                                                    <Loader2 className="w-3 h-3 animate-spin" />
                                                ) : (
                                                    <Sparkles className="w-3 h-3" />
                                                )}
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </Section>

            {/* Save Action */}
            <div className="sticky bottom-8 flex justify-center py-8">
                <button 
                    onClick={() => onSave(data)}
                    className="px-12 py-5 bg-zinc-900 text-white rounded-[32px] font-black italic flex items-center space-x-4 shadow-2xl hover:scale-105 active:scale-95 transition-all group overflow-hidden"
                >
                    <div className="relative z-10 flex items-center space-x-4">
                        <Save className="w-5 h-5" />
                        <span>SYNCHRONIZE CHANGES</span>
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/20 to-primary/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                </button>
            </div>
        </div>
    );
}
