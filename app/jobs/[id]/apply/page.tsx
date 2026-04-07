"use client";

import { useEffect, useState, use } from "react";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { 
    ChevronLeft, CheckCircle, FileText, Zap, 
    ArrowRight, BrainCircuit, Rocket, Briefcase 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Database } from "@/types/database";

type Job = Database["public"]["Tables"]["jobs"]["Row"] & {
    job_screening_questions: Database["public"]["Tables"]["job_screening_questions"]["Row"][]
};
type Resume = Database["public"]["Tables"]["resumes"]["Row"];

export default function ApplyPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const router = useRouter();
    const supabase = createClient();
    const [job, setJob] = useState<Job | null>(null);
    const [resumes, setResumes] = useState<Resume[]>([]);
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState(1);
    const [selectedResume, setSelectedResume] = useState<string | null>(null);
    const [coverLetter, setCoverLetter] = useState("");
    const [answers, setAnswers] = useState<Record<string, any>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            // Fetch Job & Questions
            const { data: jobData } = await supabase
                .from("jobs")
                .select("*, job_screening_questions(*)")
                .eq("id", id)
                .single();

            // Fetch User Resumes
            const { data: resumesData } = await supabase
                .from("resumes")
                .select("*")
                .eq("user_id", user.id);

            if (jobData) setJob(jobData as any);
            if (resumesData) {
                setResumes(resumesData);
                const primary = resumesData.find(r => r.is_primary);
                if (primary) setSelectedResume(primary.id);
                else if (resumesData.length > 0) setSelectedResume(resumesData[0].id);
            }
            setLoading(false);
        };

        fetchData();
    }, [supabase, id, router]);

    const handleAnswer = (questionId: string, val: any) => {
        setAnswers(prev => ({ ...prev, [questionId]: val }));
    };

    const submitApplication = async () => {
        setIsSubmitting(true);
        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user || !job) return;

            const { data: appData, error } = await supabase
                .from("job_applications")
                .insert({
                    job_id: job.id,
                    candidate_id: user.id,
                    resume_id: selectedResume,
                    answers: answers,
                    cover_letter: coverLetter,
                    status: "applied",
                    source: "direct",
                })
                .select()
                .single();

            if (error) throw error;

            // 2. Log Initial History
            await supabase
                .from("application_status_history")
                .insert({
                    application_id: appData.id,
                    new_status: "applied",
                    changed_by: user.id,
                    reason: "Initial submission",
                });

            setStep(4); // Success step
        } catch (error) {
            console.error("Submission failed:", error);
            alert("Application failed. You might have already applied to this job.");
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loading) return (
        <div className="flex items-center justify-center min-h-screen">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    if (!job) return <div>Job not found</div>;

    const hasQuestions = job.job_screening_questions.length > 0;

    return (
        <div className="min-h-screen bg-gray-50/30 pt-32 pb-24">
            <div className="max-w-3xl mx-auto px-6">
                
                {/* Protocol Progress */}
                <div className="flex items-center space-x-4 mb-12">
                   {[1, 2, 3, 4].map(i => (
                       <div key={i} className={`flex-1 h-2 rounded-full transition-all duration-700 ${
                           step >= i ? "bg-primary shadow-[0_0_10px_rgba(0,102,255,0.4)]" : "bg-gray-200"
                       }`} />
                   ))}
                </div>

                <AnimatePresence mode="wait">
                    {step === 1 && (
                        <motion.div
                            key="step1"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-12"
                        >
                            <div className="space-y-4">
                                <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tighter">
                                    Resume Selection <span className="text-primary tracking-normal font-body">Protocol</span>
                                </h1>
                                <p className="text-gray-500 font-bold max-w-lg">Identify the core identity matrix you wish to deploy for this specific mission.</p>
                            </div>

                            <div className="space-y-4">
                                {resumes.length > 0 ? (
                                    resumes.map(resume => (
                                        <button
                                            key={resume.id}
                                            onClick={() => setSelectedResume(resume.id)}
                                            className={`w-full p-6 bg-white border rounded-[32px] flex items-center justify-between transition-all group ${
                                                selectedResume === resume.id 
                                                    ? "border-primary ring-4 ring-primary/5 shadow-xl shadow-primary/10" 
                                                    : "border-gray-100 opacity-60 hover:opacity-100"
                                            }`}
                                        >
                                            <div className="flex items-center space-x-4">
                                                <div className={`p-4 rounded-2xl ${
                                                    selectedResume === resume.id ? "bg-primary text-white" : "bg-gray-100 text-gray-400 group-hover:bg-primary/10 group-hover:text-primary"
                                                }`}>
                                                    <FileText className="w-6 h-6" />
                                                </div>
                                                <div className="text-left">
                                                    <h4 className="text-sm font-black text-zinc-900 italic uppercase underline decoration-primary/20 decoration-2">{resume.title}</h4>
                                                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mt-1">Uploaded {new Date(resume.created_at).toLocaleDateString()}</p>
                                                </div>
                                            </div>
                                            {selectedResume === resume.id && (
                                                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white shadow-lg">
                                                    <CheckCircle className="w-5 h-5" />
                                                </div>
                                            )}
                                        </button>
                                    ))
                                ) : (
                                    <div className="bg-white border-2 border-dashed border-gray-100 rounded-[40px] p-12 text-center space-y-6">
                                        <FileText className="w-12 h-12 text-gray-200 mx-auto" />
                                        <p className="text-xs font-black text-gray-400 uppercase tracking-widest leading-relaxed">No resumes detected in your profile matrix.</p>
                                        <button className="px-8 py-3 bg-primary text-white rounded-2xl font-black text-xs uppercase tracking-widest">Upload Protocol</button>
                                    </div>
                                )}
                            </div>

                            <div className="pt-6 border-t border-gray-100 flex items-center justify-between">
                                <button
                                    onClick={() => router.back()}
                                    className="text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors flex items-center space-x-2"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                    <span>Abort mission</span>
                                </button>
                                <button
                                    disabled={!selectedResume}
                                    onClick={() => setStep(2)}
                                    className="px-10 py-5 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic shadow-2xl hover:scale-105 active:scale-95 transition-all flex items-center space-x-3 disabled:opacity-30 disabled:cursor-not-allowed"
                                >
                                    <span>Continue Protocol</span>
                                    <ArrowRight className="w-4 h-4" />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 2 && (
                         <motion.div
                            key="step2"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-12"
                        >
                            <div className="space-y-4">
                                <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tighter">
                                    Cover Letter <span className="text-primary tracking-normal font-body">Optional</span>
                                </h1>
                                <p className="text-gray-500 font-bold max-w-lg">Narrate your mission experience and value proposition to the organization.</p>
                            </div>

                            <div className="space-y-6">
                                <div className="p-1.5 bg-gray-50 rounded-[40px] border border-gray-100 shadow-inner group">
                                     <textarea 
                                        rows={12}
                                        value={coverLetter}
                                        onChange={(e) => setCoverLetter(e.target.value)}
                                        className="w-full bg-white border border-gray-100 rounded-[32px] px-8 py-8 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all resize-none shadow-sm placeholder:text-gray-300 italic"
                                        placeholder="Dear Hiring Matrix... (Optional)"
                                     />
                                </div>
                                <div className="flex items-center space-x-2 text-[10px] font-black text-gray-400 uppercase tracking-widest ml-6">
                                     <Zap className="w-3 h-3 text-primary" />
                                     <span>Tip: Keep it concise and mission-focused.</span>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-gray-100 flex items-center justify-between">
                                <button
                                    onClick={() => setStep(1)}
                                    className="text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors flex items-center space-x-2"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                    <span>Resume Selector</span>
                                </button>
                                <button
                                    onClick={() => hasQuestions ? setStep(3) : submitApplication()}
                                    className="px-10 py-5 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic shadow-2xl hover:scale-105 active:scale-95 transition-all flex items-center space-x-3"
                                >
                                    <span>{hasQuestions ? "Continue Protocol" : "Initialize Deployment"}</span>
                                    {hasQuestions ? <ArrowRight className="w-4 h-4" /> : <Rocket className="w-4 h-4" />}
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 3 && (
                        <motion.div
                            key="step3"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="space-y-12"
                        >
                            <div className="space-y-4">
                                <h1 className="text-4xl font-black font-display text-zinc-900 italic tracking-tighter">
                                    Discovery <span className="text-primary tracking-normal font-body">Vetting</span>
                                </h1>
                                <p className="text-gray-500 font-bold max-w-lg">Answer the screening protocols required by the organization to finalize your deployment.</p>
                            </div>

                            <div className="space-y-10">
                                {job.job_screening_questions.map((q, idx) => (
                                    <div key={q.id} className="space-y-6">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center font-black text-xs italic">
                                                {idx + 1}
                                            </div>
                                            <h4 className="text-sm font-black text-zinc-900 italic uppercase underline decoration-primary/10 decoration-4 underline-offset-4">{q.question} {q.is_required && <span className="text-primary">*</span>}</h4>
                                        </div>

                                        {q.input_type === 'short_text' && (
                                            <input 
                                                type="text"
                                                onChange={(e) => handleAnswer(q.id, e.target.value)}
                                                className="w-full bg-white border border-gray-100 rounded-2xl px-6 py-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all"
                                                placeholder="Enter response..."
                                            />
                                        )}

                                        {q.input_type === 'long_text' && (
                                           <textarea 
                                                rows={4}
                                                onChange={(e) => handleAnswer(q.id, e.target.value)}
                                                className="w-full bg-white border border-gray-100 rounded-[28px] px-6 py-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all resize-none"
                                                placeholder="Detailed response matrix..."
                                           />
                                        )}

                                        {q.input_type === 'yes_no' && (
                                            <div className="flex space-x-4">
                                                {['Yes', 'No'].map(opt => (
                                                    <button
                                                        key={opt}
                                                        onClick={() => handleAnswer(q.id, opt)}
                                                        className={`px-8 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all ${
                                                            answers[q.id] === opt 
                                                                ? "bg-primary text-white shadow-xl shadow-primary/20" 
                                                                : "bg-white border border-gray-100 text-gray-400 hover:border-primary/50"
                                                        }`}
                                                    >
                                                        {opt}
                                                    </button>
                                                ))}
                                            </div>
                                        )}

                                        {q.input_type === 'multiple_choice' && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {(q.options as string[])?.map(opt => (
                                                    <button
                                                        key={opt}
                                                        onClick={() => handleAnswer(q.id, opt)}
                                                        className={`p-4 rounded-2xl border text-left flex items-center space-x-3 transition-all ${
                                                            answers[q.id] === opt 
                                                                ? "bg-primary/5 border-primary text-primary" 
                                                                : "bg-white border-gray-100 text-gray-500 hover:bg-gray-50"
                                                        }`}
                                                    >
                                                        <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                                                            answers[q.id] === opt ? "border-primary" : "border-gray-200"
                                                        }`}>
                                                            {answers[q.id] === opt && <div className="w-1.5 h-1.5 bg-primary rounded-full transition-all" />}
                                                        </div>
                                                        <span className="text-xs font-bold leading-none">{opt}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            <div className="pt-6 border-t border-gray-100 flex items-center justify-between">
                                <button
                                    onClick={() => setStep(2)}
                                    className="text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-primary transition-colors flex items-center space-x-2"
                                >
                                    <ChevronLeft className="w-4 h-4" />
                                    <span>Cover Letter Matrix</span>
                                </button>
                                <button
                                    disabled={isSubmitting}
                                    onClick={submitApplication}
                                    className="px-12 py-5 bg-primary text-white rounded-[24px] font-black text-sm uppercase tracking-widest italic shadow-2xl shadow-primary/30 hover:scale-105 active:scale-95 transition-all flex items-center space-x-3 disabled:opacity-50"
                                >
                                    {isSubmitting ? (
                                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    ) : (
                                        <>
                                            <span>Initialize Deployment</span>
                                            <Rocket className="w-4 h-4" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 4 && (
                         <motion.div
                            key="step4"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-white border border-gray-100 rounded-[64px] p-16 text-center shadow-2xl space-y-10 relative overflow-hidden"
                         >
                            <div className="absolute inset-0 bg-primary opacity-[0.01]" />
                            <div className="relative z-10 w-24 h-24 bg-primary rounded-[32px] flex items-center justify-center mx-auto shadow-2xl shadow-primary/30">
                                <CheckCircle className="w-12 h-12 text-white" />
                            </div>
                            <div className="relative z-10 space-y-4">
                                <h2 className="text-4xl font-black font-display text-zinc-900 italic tracking-tighter">Application Successful.</h2>
                                <p className="text-gray-500 font-bold max-w-sm mx-auto">Your identity matrix has been transmitted to the organization. Monitor your dashboard for protocol updates.</p>
                            </div>
                            <div className="relative z-10 flex flex-col items-center gap-4">
                                <button 
                                    onClick={() => router.push("/dashboard")}
                                    className="px-12 py-5 bg-zinc-900 text-white rounded-[24px] font-black text-xs uppercase tracking-widest italic shadow-xl hover:scale-105 transition-all"
                                >
                                    Return to Command Center
                                </button>
                                <button 
                                    onClick={() => router.push("/jobs")}
                                    className="text-[10px] font-black text-gray-400 uppercase tracking-widest hover:text-primary transition-colors"
                                >
                                    Discover new missions
                                </button>
                            </div>
                         </motion.div>
                    )}
                </AnimatePresence>

                {/* Job Summary Banner (Static) */}
                {step < 4 && (
                    <div className="mt-12 bg-white/50 backdrop-blur-xl border border-white rounded-[32px] p-6 flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                            <div className="w-10 h-10 border border-gray-100 rounded-xl flex items-center justify-center font-black text-xs text-gray-300">
                                {job.title.substring(0, 1)}
                            </div>
                            <div>
                                <p className="text-[8px] font-black uppercase tracking-widest text-gray-400">Target Opportunity</p>
                                <h5 className="text-sm font-black text-zinc-900 italic">{job.title}</h5>
                            </div>
                        </div>
                        <div className="flex items-center space-x-2 text-primary font-black italic text-sm">
                             <Briefcase className="w-4 h-4" />
                             <span>{job.job_type}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
