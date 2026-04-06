"use client";

import { useEffect, useState, use } from "react";
import { 
    ChevronLeft, 
    Sparkles, 
    Download, 
    Share2, 
    History,
    Zap,
    Layout
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ResumeEditor from "@/components/resumes/ResumeEditor";
import AuditPanel from "@/components/resumes/AuditPanel";
import RewriteWorkspace from "@/components/resumes/RewriteWorkspace";
import ResumeTemplate from "@/components/resumes/ResumeTemplate";
import TemplateSwitcher from "@/components/resumes/TemplateSwitcher";
import { PDFDownloadLink } from "@react-pdf/renderer";
import { PDFTemplate } from "@/components/resumes/PDFTemplate";

export default function ResumeDetailPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const [resume, setResume] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [viewMode, setViewMode] = useState<'edit' | 'preview'>('edit');
    const [showRewriter, setShowRewriter] = useState(false);
    const [optimizationData, setOptimizationData] = useState<any>(null);
    const [optimizing, setOptimizing] = useState(false);

    const fetchResume = async () => {
        try {
            const response = await fetch(`/api/resumes/${id}`);
            const data = await response.json();
            if (response.ok) {
                setResume(data);
                // Initial optimization trigger
                handleOptimize(data.parsed_content);
            }
        } catch (error) {
            console.error("Fetch failed:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleOptimize = async (content: any) => {
        setOptimizing(true);
        try {
            const response = await fetch(`/api/resumes/${id}/optimize`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ resumeContent: content })
            });
            const data = await response.json();
            if (response.ok) setOptimizationData(data);
        } catch (error) {
            console.error("Optimization failed:", error);
        } finally {
            setOptimizing(false);
        }
    };

    useEffect(() => {
        fetchResume();
    }, [id]);

    const handleSave = async (updatedContent: any) => {
        setSaving(true);
        try {
            const response = await fetch(`/api/resumes/${id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ parsed_content: updatedContent })
            });
            if (response.ok) {
                const updated = await response.json();
                setResume(updated);
            }
        } catch (error) {
            console.error("Save failed:", error);
        } finally {
            setSaving(false);
        }
    };

    const handleInlineAICall = async (path: string, content: any) => {
        try {
            const response = await fetch(`/api/resumes/${id}/rewrite`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    section: path,
                    content: typeof content === 'string' ? content : JSON.stringify(content),
                    jobDescription: "Optimize for professional impact and specific industry standards."
                })
            });
            const data = await response.json();
            if (response.ok) {
                return data.rewritten;
            }
        } catch (error) {
            console.error("Inline AI failed:", error);
        }
        return "";
    };

    if (loading) return (
        <div className="flex items-center justify-center h-screen bg-gray-50/50">
            <div className="flex flex-col items-center space-y-4">
                <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-gray-400">Loading DNA Structure...</p>
            </div>
        </div>
    );

    if (!resume) return <div>Resume not found.</div>;

    // Mock scores for now (to be replaced by optimization API)
    const auditData = {
        score: 84,
        metrics: { impact: 76, verbs: 92, keywords: 65 },
        suggestions: [
            { category: "Impact", title: "Quantify metrics in experience", description: "Use more percentages and dollar amounts to show impact." },
            { category: "ATS", title: "Target Cloud Architecture keywords", description: "Your profile lacks specific mention of AWS Lambda and Terraform." },
            { category: "Verbs", title: "Replace passive voice", description: "Change 'responsible for' to 'spearheaded' or 'orchestrated'." }
        ]
    };

    return (
        <div className="min-h-screen bg-gray-50/50 pb-20">
            {/* Top Navigation Bar */}
            <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-gray-100 px-8 py-4">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center space-x-6">
                        <button 
                            onClick={() => window.location.href = "/dashboard/resumes"}
                            className="p-3 bg-gray-100 hover:bg-gray-200 rounded-2xl transition-all"
                        >
                            <ChevronLeft className="w-4 h-4 text-zinc-900" />
                        </button>
                        <div>
                            <h2 className="text-xl font-black font-display italic uppercase tracking-tighter text-zinc-900 leading-none">
                                {resume.title}
                            </h2>
                            <div className="flex items-center space-x-3 mt-1.5">
                                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                                <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest leading-none">
                                    V1.0 • AI-SYNTHESIZED {new Date(resume.created_at).toLocaleDateString()}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-3">
                         <button className="p-3 bg-white border border-gray-100 hover:bg-gray-50 rounded-2xl transition-all shadow-sm">
                            <History className="w-4 h-4 text-gray-400" />
                         </button>
                         <button className="px-6 py-3 bg-white border border-gray-100 hover:bg-gray-50 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all shadow-sm flex items-center space-x-2">
                            <Download className="w-4 h-4" />
                            <span>EXPORT PDF</span>
                         </button>
                         <button 
                            onClick={() => setShowRewriter(true)}
                            className="px-6 py-3 bg-primary text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:scale-105 transition-all shadow-lg flex items-center space-x-2"
                         >
                            <Sparkles className="w-4 h-4" />
                            <span>TAILOR TO JOB</span>
                         </button>
                    </div>
                </div>
            </header>

            <AnimatePresence>
                {showRewriter && (
                    <RewriteWorkspace 
                        resumeId={id}
                        sections={resume.parsed_content}
                        onClose={() => setShowRewriter(false)}
                        currentTheme={resume.template_settings?.theme || 'modern'}
                        onApply={async (section, newSectionContent) => {
                            if (!resume || !resume.parsed_content) return;
                            
                            const updatedParsedContent = { ...resume.parsed_content };
                            
                            if (section === 'full') {
                                // Full Evolution: Replace primary sections with tailored narrative 
                                // For simplicity in this v2, we'll store the full tailored text in the summary 
                                // and clear or minimize other sections for the synthesis view
                                updatedParsedContent.summary = newSectionContent;
                                updatedParsedContent.experience = []; // Synthesis focus on the narrative
                                updatedParsedContent.skills = "" as any; 
                            } else {
                                // Surgical Evolution: Update specific segment
                                updatedParsedContent[section] = newSectionContent; 
                            }

                            // Ask user if they want to save as a new version or update current
                            const saveAsNew = confirm("Would you like to save this as a NEW Targeted Synthesis?\n(Cancel to update current Master DNA)");

                            if (saveAsNew) {
                                const label = prompt("Enter a label for this Synthesis (e.g. 'Senior Dev @ Google'):", "New Targeted Synthesis");
                                if (!label) return;

                                const response = await fetch("/api/resumes", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        title: label,
                                        version_label: label,
                                        parent_id: id,
                                        parsed_content: updatedParsedContent,
                                        template_settings: resume.template_settings,
                                        status: 'parsed'
                                    })
                                });

                                if (response.ok) {
                                    const newVersion = await response.json();
                                    window.location.href = `/dashboard/resumes/${newVersion.id}`;
                                }
                            } else {
                                handleSave(updatedParsedContent);
                                setShowRewriter(false);
                            }
                        }}
                    />
                )}
            </AnimatePresence>

            <main className="max-w-7xl mx-auto px-8 py-10">
                <div className="flex flex-col lg:flex-row gap-10">
                    {/* Primary Content Area (Editor) */}
                    <div className="flex-grow lg:w-[65%] order-2 lg:order-1">
                        <div className="flex items-center space-x-4 mb-10">
                            <button 
                                onClick={() => setViewMode('edit')}
                                className={`px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                                    viewMode === 'edit' ? "bg-zinc-900 text-white shadow-xl scale-105" : "bg-white text-gray-400 hover:bg-gray-50"
                                }`}
                            >
                                <div className="flex items-center space-x-2">
                                    <Layout className="w-4 h-4" />
                                    <span>STRUCTURE EDITOR</span>
                                </div>
                            </button>
                            <button 
                                onClick={() => setViewMode('preview')}
                                className={`px-8 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all ${
                                    viewMode === 'preview' ? "bg-zinc-900 text-white shadow-xl scale-105" : "bg-white text-gray-400 hover:bg-gray-50"
                                }`}
                            >
                                <div className="flex items-center space-x-2">
                                    <Sparkles className="w-4 h-4" />
                                    <span>PROFESSIONAL PREVIEW</span>
                                </div>
                            </button>
                        </div>

                        <AnimatePresence mode="wait">
                            <motion.div
                                key={viewMode}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3 }}
                            >
                                {viewMode === 'edit' ? (
                                    <ResumeEditor 
                                        initialData={resume.parsed_content} 
                                        onSave={handleSave} 
                                        onAICall={handleInlineAICall}
                                    />
                                ) : (
                                    <div className="space-y-6">
                                        <div className="flex justify-end">
                                            <PDFDownloadLink
                                                document={<PDFTemplate data={resume.parsed_content} />}
                                                fileName={`${resume.parsed_content.fullName.split(' ').join('_')}_Resume.pdf`}
                                                className="px-8 py-3 bg-primary text-white rounded-2xl text-[10px] font-black uppercase tracking-widest flex items-center space-x-2 hover:scale-105 transition-all shadow-xl"
                                            >
                                                {/* @ts-ignore */}
                                                {({ loading }) => (
                                                    <div className="flex items-center space-x-2">
                                                        <Download className="w-4 h-4" />
                                                        <span>{loading ? "ENCODING DNA..." : "DOWNLOAD COLD STORAGE"}</span>
                                                    </div>
                                                )}
                                            </PDFDownloadLink>
                                        </div>
                                        <div className="bg-white border p-12 rounded-[40px] aspect-[1/1.414] shadow-2xl relative overflow-y-auto scrollbar-hide">
                                            <ResumeTemplate 
                                                data={resume.parsed_content} 
                                                theme={resume.template_settings?.theme || 'modern'} 
                                            />
                                        </div>
                                    </div>
                                )}
                            </motion.div>
                        </AnimatePresence>
                    </div>

                    {/* Meta Info Sidebar (Audit Panel) */}
                    <aside className="lg:w-[35%] order-1 lg:order-2 space-y-8">
                         <TemplateSwitcher 
                            current={resume.template_settings?.theme || 'modern'}
                            onSelect={async (theme) => {
                                const newSettings = { ...(resume.template_settings || {}), theme };
                                setResume({ ...resume, template_settings: newSettings });
                                await fetch(`/api/resumes/${id}`, {
                                    method: "PATCH",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ template_settings: newSettings })
                                });
                            }}
                         />
                         <AuditPanel 
                             score={optimizationData?.score || 0}
                             metrics={optimizationData?.metrics || { impact: 0, verbs: 0, keywords: 0 }}
                             suggestions={optimizationData?.suggestions || []}
                         />
                         {optimizing && (
                            <div className="mt-4 flex items-center justify-center space-x-3 text-[10px] font-black uppercase tracking-widest text-primary animate-pulse">
                                <Zap className="w-3 h-3" />
                                <span>AI RE-AUDITING DNA...</span>
                            </div>
                         )}
                    </aside>
                </div>
            </main>
        </div>
    );
}
