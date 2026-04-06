"use client";

import { useState } from "react";
import { 
    Sparkles, 
    ChevronLeft, 
    Zap, 
    ArrowRight, 
    Check, 
    RotateCcw,
    Target,
    FileText,
    Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface RewriteWorkspaceProps {
    resumeId: string;
    sections: any;
    onClose: () => void;
    onApply: (section: string, updatedContent: any) => void;
    currentTheme?: string;
}

export default function RewriteWorkspace({ resumeId, sections, onClose, onApply, currentTheme = 'modern' }: RewriteWorkspaceProps) {
    const [step, setStep] = useState<1 | 2>(1);
    const [jobDescription, setJobDescription] = useState("");
    const [jobUrl, setJobUrl] = useState("");
    const [isExtracting, setIsExtracting] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [selectedSection, setSelectedSection] = useState<string | null>(null);
    const [rewrittenContent, setRewrittenContent] = useState<any>(null);

    const handleExtract = async () => {
        if (!jobUrl) return;
        setIsExtracting(true);
        try {
            const response = await fetch("/api/ai/extract-job", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: jobUrl })
            });
            const data = await response.json();
            if (response.ok) {
                setJobDescription(data.extracted);
            }
        } catch (error) {
            console.error("Extraction failed:", error);
        } finally {
            setIsExtracting(false);
        }
    };

    const handleRewrite = async (sectionKey: string | 'full') => {
        setIsThinking(true);
        if (sectionKey !== 'full') setSelectedSection(sectionKey);
        
        // Extract human-readable content to avoid JSON responses
        let contentToRewrite = "";
        if (sectionKey === 'full') {
            contentToRewrite = "WHOLE_RESUME";
        } else {
            const rawContent = sections[sectionKey];
            if (typeof rawContent === 'object') {
                // If it's a structured object (like skills), simplify it for the AI
                contentToRewrite = JSON.stringify(rawContent, null, 2); 
                // We'll trust the new strict API prompt to handle this string cleanly
            } else {
                contentToRewrite = rawContent;
            }
        }

        try {
            const response = await fetch(`/api/resumes/${resumeId}/rewrite`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    section: sectionKey,
                    content: contentToRewrite,
                    jobDescription,
                    fullEvolution: sectionKey === 'full',
                    template: currentTheme,
                    metricsFocus: "quantifiable impact and industry-specific keywords"
                })
            });
            const data = await response.json();
            if (response.ok) {
                setRewrittenContent(data.rewritten);
                setStep(2);
            }
        } catch (error) {
            console.error("Rewrite failed:", error);
        } finally {
            setIsThinking(false);
        }
    };

    return (
        <div className="absolute inset-0 z-50 bg-white flex flex-col md:flex-row overflow-hidden">
            {/* Left Sidebar: Original Content Navigation */}
            <aside className="w-full md:w-80 bg-gray-50 border-r border-gray-100 p-8 flex flex-col">
                <button 
                    onClick={onClose}
                    className="flex items-center space-x-2 text-gray-400 hover:text-zinc-900 transition-colors mb-12 group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span className="text-[10px] font-black uppercase tracking-widest">Back to Lab</span>
                </button>

                <h3 className="text-sm font-black italic uppercase tracking-widest text-zinc-900 mb-8 px-2">DNA Segments</h3>
                
                <nav className="space-y-2 flex-grow overflow-y-auto pr-2 custom-scrollbar">
                    {Object.keys(sections).map((key) => (
                        <button
                            key={key}
                            onClick={() => setSelectedSection(key)}
                            className={`w-full text-left p-5 rounded-2xl transition-all flex items-center justify-between group ${
                                selectedSection === key ? "bg-white text-zinc-900 shadow-sm ring-1 ring-gray-100" : "text-gray-400 hover:bg-gray-100"
                            }`}
                        >
                            <span className="text-[10px] font-black uppercase tracking-widest">{key}</span>
                            {selectedSection === key ? <Target className="w-4 h-4 text-primary" /> : <div className="w-1.5 h-1.5 bg-gray-200 rounded-full group-hover:bg-gray-400" />}
                        </button>
                    ))}
                </nav>

                <div className="mt-auto p-4 bg-primary/5 border border-primary/10 rounded-2xl">
                    <div className="flex items-center space-x-3 text-primary mb-2">
                        <Zap className="w-4 h-4" />
                        <span className="text-[10px] font-black uppercase tracking-widest leading-none mt-1">AI Protocol Ready</span>
                    </div>
                </div>
            </aside>

            {/* Main Content Area: Split Workspace */}
            <main className="flex-grow flex flex-col">
                {/* Protocol Header */}
                <header className="px-10 py-6 border-b border-gray-100 flex items-center justify-between bg-white/50 backdrop-blur-md">
                    <div className="flex items-center space-x-4">
                        <div className="p-2 bg-zinc-900 text-white rounded-lg">
                            <Sparkles className="w-4 h-4" />
                        </div>
                        <h2 className="text-xs font-black italic uppercase tracking-widest text-zinc-900">AI Rewriting Workspace</h2>
                        <div className="h-4 w-[1px] bg-gray-200 mx-2"></div>
                        <span className="text-[9px] font-black uppercase tracking-widest text-primary bg-primary/5 px-3 py-1 rounded-full border border-primary/10">
                            Adapting to {currentTheme} Persona
                        </span>
                    </div>
                    {step === 2 && (
                         <button 
                            onClick={() => setStep(1)}
                            className="text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-zinc-900 flex items-center space-x-2"
                        >
                            <RotateCcw className="w-3 h-3" />
                            <span>REDESIGN TARGET</span>
                        </button>
                    )}
                </header>

                <div className="flex-grow flex overflow-hidden">
                    {/* Workspace: Comparison View */}
                    <AnimatePresence mode="wait">
                        {step === 1 ? (
                            <motion.div 
                                key="step1"
                                className="w-full flex"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                            >
                                {/* Target Input */}
                                <div className="flex-grow p-12 bg-white flex flex-col max-w-4xl mx-auto">
                                    <div className="mb-10 text-center">
                                        <h1 className="text-5xl font-black font-display text-zinc-900 italic uppercase tracking-tighter leading-none mb-4">Target Job DNA</h1>
                                        <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Input the job description to align your resume professionally</p>
                                    </div>
                                    
                                    <div className="space-y-4 mb-8">
                                        <div className="flex space-x-3">
                                            <div className="relative flex-grow">
                                                <input 
                                                    type="text"
                                                    placeholder="Paste Job URL or Raw Job Description here..."
                                                    className="w-full bg-gray-50 border-none rounded-2xl px-6 py-4 font-bold text-zinc-900 focus:ring-2 focus:ring-primary/20 outline-none placeholder:text-gray-300 transition-all"
                                                    value={jobUrl}
                                                    onChange={(e) => setJobUrl(e.target.value)}
                                                    onKeyDown={(e) => e.key === 'Enter' && handleExtract()}
                                                />
                                                {isExtracting && (
                                                    <div className="absolute right-4 top-1/2 -translate-y-1/2">
                                                        <Loader2 className="w-4 h-4 animate-spin text-primary" />
                                                    </div>
                                                )}
                                            </div>
                                            <button 
                                                onClick={handleExtract}
                                                disabled={!jobUrl || isExtracting}
                                                className="px-8 bg-zinc-900 text-white rounded-2xl font-black italic text-[10px] uppercase tracking-widest hover:bg-zinc-800 transition-all disabled:opacity-50 min-w-[180px]"
                                            >
                                                {isExtracting ? "ENCODING DNA..." : "INITIATE SYNTHESIS"}
                                            </button>
                                        </div>

                                        <div className="relative flex items-center py-4">
                                            <div className="flex-grow border-t border-gray-100"></div>
                                            <span className="flex-shrink mx-4 text-[9px] font-black text-gray-300 uppercase tracking-widest text-center px-4 leading-none">THE SYNTHESIZED DNA WILL APPEAR BELOW FOR EDITING</span>
                                            <div className="flex-grow border-t border-gray-100"></div>
                                        </div>

                                        <textarea 
                                            className="w-full h-64 bg-gray-50 border-2 border-dashed border-gray-100 rounded-[40px] p-10 text-gray-500 font-medium leading-relaxed focus:border-primary/30 focus:bg-primary/5 outline-none transition-all resize-none shadow-inner"
                                            placeholder="The synthesized Job DNA will be generated here for your review..."
                                            value={jobDescription}
                                            onChange={(e) => setJobDescription(e.target.value)}
                                        />
                                    </div>
                                    
                                    <div className="flex flex-col items-center space-y-6">
                                        <button 
                                            onClick={() => handleRewrite('full')}
                                            disabled={!jobDescription || isThinking}
                                            className="px-20 py-8 bg-zinc-900 text-white rounded-[40px] font-black italic flex flex-col items-center space-y-2 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.3)] hover:scale-105 active:scale-95 transition-all group relative overflow-hidden disabled:opacity-50 disabled:scale-100"
                                        >
                                            {isThinking && !selectedSection ? (
                                                <>
                                                    <Loader2 className="w-6 h-6 animate-spin" />
                                                    <span className="text-xs uppercase tracking-tighter">SYNTHESIZING WHOLE DNA...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <div className="flex items-center space-x-3">
                                                        <Zap className="w-5 h-5 text-primary fill-primary" />
                                                        <span className="text-xl">WHOLE DNA EVOLUTION</span>
                                                    </div>
                                                    <span className="text-[9px] text-gray-400 uppercase tracking-widest font-black leading-none italic pb-1">Tailor ENTIRE Resume in one pass</span>
                                                </>
                                            )}
                                        </button>

                                        <div className="flex items-center space-x-6">
                                            <div className="h-[1px] w-12 bg-gray-100"></div>
                                            <span className="text-[9px] font-black text-gray-300 uppercase tracking-[0.3em]">OR SURGICAL POLISH</span>
                                            <div className="h-[1px] w-12 bg-gray-100"></div>
                                        </div>

                                        <button 
                                            onClick={() => selectedSection && handleRewrite(selectedSection)}
                                            disabled={!jobDescription || !selectedSection || isThinking}
                                            className="px-12 py-5 bg-white border-2 border-gray-100 text-zinc-900 rounded-[32px] font-black italic flex items-center space-x-4 hover:border-zinc-900 transition-all disabled:opacity-50"
                                        >
                                            {isThinking && selectedSection ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin" />
                                                    <span>POLISHING SEGMENT...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles className="w-4 h-4 text-zinc-400" />
                                                    <span>EVOLVE SELECTED SEGMENT</span>
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div 
                                key="step2"
                                className="w-full flex flex-col md:flex-row overflow-hidden"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                            >
                                {/* Comparative Panes */}
                                <div className="flex-1 p-10 bg-gray-50/50 border-r border-gray-100 overflow-y-auto custom-scrollbar">
                                    <div className="mb-8 flex items-center justify-between">
                                        <h4 className="text-[10px] font-black uppercase tracking-widest text-gray-400">Current DNA Segment</h4>
                                        <span className="px-3 py-1 bg-gray-100 text-gray-400 rounded-full text-[9px] font-black">ORIGINAL</span>
                                    </div>
                                    <pre className="text-sm text-gray-500 font-medium whitespace-pre-wrap leading-relaxed">
                                        {JSON.stringify(sections[selectedSection || ""], null, 2)}
                                    </pre>
                                </div>

                                <div className="flex-1 p-10 bg-white overflow-y-auto custom-scrollbar relative">
                                    <div className="mb-8 flex items-center justify-between">
                                        <h4 className="text-[10px] font-black uppercase tracking-widest text-primary">Evolved Segment Output</h4>
                                        <div className="flex items-center space-x-2">
                                            <Sparkles className="w-4 h-4 text-primary" />
                                            <span className="text-[9px] font-black uppercase tracking-widest text-primary">AI OPTIMIZED</span>
                                        </div>
                                    </div>
                                    <div className="prose prose-sm max-w-none text-zinc-900 font-medium leading-loose">
                                        {rewrittenContent}
                                    </div>

                                    {/* Action Footers */}
                                    <div className="sticky bottom-0 mt-20 pt-10 pb-6 bg-gradient-to-t from-white via-white to-transparent flex justify-center space-x-4">
                                        <button 
                                            onClick={() => setStep(1)}
                                            className="px-8 py-4 bg-gray-50 text-gray-400 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:text-zinc-900 hover:bg-gray-100 transition-all"
                                        >
                                            DISCARD
                                        </button>
                                        <button 
                                            onClick={() => selectedSection && onApply(selectedSection, rewrittenContent)}
                                            className="px-12 py-4 bg-zinc-900 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-105 transition-all flex items-center space-x-3 shadow-xl"
                                        >
                                            <Check className="w-4 h-4 text-primary" />
                                            <span>INTEGRATE TO BASE DNA</span>
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </main>
        </div>
    );
}
