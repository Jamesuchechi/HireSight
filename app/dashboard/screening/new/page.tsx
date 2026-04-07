"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Upload, X, CheckCircle2, 
    ArrowRight, Rocket, SlidersHorizontal, 
    BrainCircuit, Target, Zap, FileText,
    ChevronLeft, Loader2, MessageSquare,
    Users, Database, MousePointer2
} from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

export default function NewScreeningPage() {
    const supabase = createClient();
    const router = useRouter();
    const [jobs, setJobs] = useState<any[]>([]);
    const [selectedJob, setSelectedJob] = useState("");
    const [title, setTitle] = useState("");
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [screeningMode, setScreeningMode] = useState<'bulk' | 'job'>('bulk');
    const [applicants, setApplicants] = useState<any[]>([]);
    const [selectedApplicants, setSelectedApplicants] = useState<Set<string>>(new Set());

    const [weights, setWeights] = useState({
        skills: 30,
        experience: 20,
        education: 15,
        keywords: 15,
        questions: 10,
        assessments: 10
    });

    const [jobQuestions, setJobQuestions] = useState<any[]>([]);
    const [questionsConfig, setQuestionsConfig] = useState<any>({});

    const [criteria, setCriteria] = useState({
        requiredSkills: "",
        niceToHaveSkills: "",
        minExperience: 0,
        educationLevel: "Bachelor's",
        keywords: ""
    });

    useEffect(() => {
        const fetchJobs = async () => {
            const { data } = await supabase.from("jobs").select("id, title").eq("status", "active");
            if (data) setJobs(data);
        };
        fetchJobs();
    }, [supabase]);

    useEffect(() => {
        const fetchJobQuestions = async () => {
            if (!selectedJob) {
                setJobQuestions([]);
                return;
            }
            const { data } = await supabase
                .from("job_screening_questions")
                .select("*")
                .eq("job_id", selectedJob)
                .order("order_index", { ascending: true });
            
            if (data) {
                setJobQuestions(data);
                // Initialize config
                const initialConfig: any = {};
                data.forEach(q => {
                    initialConfig[q.question] = { value: "", keywords: "" };
                });
                setQuestionsConfig(initialConfig);
            }
        };

        const fetchApplicants = async () => {
            if (!selectedJob) {
                setApplicants([]);
                return;
            }
            const { data } = await supabase
                .from("job_applications")
                .select(`
                    id,
                    profiles:candidate_id (full_name, avatar_url, headline),
                    resumes:resume_id (id, file_url)
                `)
                .eq("job_id", selectedJob);
            
            if (data) {
                setApplicants(data);
                // Auto-select those with resumes
                const withResumes = data
                    .filter(a => {
                        const resume = Array.isArray(a.resumes) ? a.resumes[0] : a.resumes;
                        return resume?.file_url;
                    })
                    .map(a => a.id);
                setSelectedApplicants(new Set(withResumes));
            }
        };

        fetchJobQuestions();
        fetchApplicants();
    }, [supabase, selectedJob]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files).filter(f => f.type === "application/pdf");
            setFiles(prev => [...prev, ...newFiles].slice(0, 50));
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    const toggleApplicant = (id: string) => {
        setSelectedApplicants(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const startScreening = async () => {
        if (!title) {
            alert("Please provide a title for this neural cycle.");
            return;
        }
        
        if (screeningMode === 'bulk' && files.length === 0) {
            alert("No resume matrices provided for vetting.");
            return;
        }

        if (screeningMode === 'job' && selectedApplicants.size === 0) {
            alert("No candidates selected for sync.");
            return;
        }

        setUploading(true);

        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const fileData: { name: string, url: string }[] = [];

            if (screeningMode === 'bulk') {
                // 1. Upload files to Storage
                for (const file of files) {
                    const filePath = `${user.id}/${Date.now()}-${file.name}`;
                    const { data: uploadData, error: uploadError } = await supabase.storage
                        .from("screening-resumes")
                        .upload(filePath, file);
                    
                    if (uploadError) throw uploadError;

                    const { data: { publicUrl } } = supabase.storage
                        .from("screening-resumes")
                        .getPublicUrl(filePath);
                    
                    fileData.push({ name: file.name, url: publicUrl });
                }
            } else {
                // 1. Collect Existing URLs
                const selected = applicants.filter(a => selectedApplicants.has(a.id));
                selected.forEach(a => {
                    const resume = Array.isArray(a.resumes) ? a.resumes[0] : a.resumes;
                    if (resume?.file_url) {
                        fileData.push({ 
                            name: a.profiles?.full_name || "Applicant", 
                            url: resume.file_url 
                        });
                    }
                });
            }

            // 2. Create Screening Session
            const sessionResponse = await fetch("/api/screening/create", {
                method: "POST",
                body: JSON.stringify({
                    title,
                    jobId: selectedJob || null,
                    totalFiles: fileData.length,
                    criteria: {
                        requiredSkills: criteria.requiredSkills.split(",").map(s => s.trim()).filter(Boolean),
                        niceToHaveSkills: criteria.niceToHaveSkills.split(",").map(s => s.trim()).filter(Boolean),
                        minExperience: criteria.minExperience,
                        educationLevel: criteria.educationLevel,
                        keywords: criteria.keywords.split(",").map(s => s.trim()).filter(Boolean),
                        weights: {
                            skills: weights.skills,
                            experience: weights.experience,
                            education: weights.education,
                            keywords: weights.keywords
                        }
                    },
                    weightQuestions: weights.questions,
                    weightAssessments: weights.assessments,
                    questionsConfig
                })
            });

            const session = await sessionResponse.json();
            if (session.error) throw new Error(session.error);

            // 3. Begin Processing (Client-Side Orchestrator to avoid timeouts)
            setUploading(false);
            setProcessing(true);
            
            let completedCount = 0;
            // Process in small batches of 3 to avoid AI rate limits but stay fast
            const batchSize = 3;
            for (let i = 0; i < fileData.length; i += batchSize) {
                const batch = fileData.slice(i, i + batchSize);
                await Promise.all(batch.map(async (file) => {
                    try {
                        const res = await fetch("/api/screening/process", {
                            method: "POST",
                            body: JSON.stringify({
                                sessionId: session.id,
                                resumeUrl: file.url
                            })
                        });
                        const data = await res.json();
                        if (data.error) console.error(`Error processing ${file.name}:`, data.error);
                    } catch (err) {
                        console.error(`Network error for ${file.name}:`, err);
                    } finally {
                        completedCount++;
                        setProgress(Math.round((completedCount / fileData.length) * 100));
                    }
                }));
            }

            // 4. Redirect on completion
            router.push(`/dashboard/screening/${session.id}`);

        } catch (error: any) {
            console.error("Screening Failed:", error);
            alert(`Failed: ${error.message}`);
            setUploading(false);
            setProcessing(false);
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-24">
             {/* Header */}
             <header className="flex flex-col space-y-8">
                <Link 
                    href="/dashboard/screening" 
                    className="inline-flex items-center space-x-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-secondary transition-colors group"
                >
                    <ChevronLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                    <span>Back to Cycle History</span>
                </Link>

                <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-8">
                    <div className="space-y-4">
                        <div className="flex items-center space-x-3 text-secondary">
                             <BrainCircuit className="w-8 h-8" />
                             <span className="text-sm font-black uppercase tracking-widest italic decoration-2 underline decoration-secondary/20">Metric Extraction Engine</span>
                        </div>
                        <h1 className="text-4xl md:text-6xl font-black font-display text-zinc-900 italic tracking-tighter">
                            New Neural <span className="text-secondary tracking-normal">Cycle</span>
                        </h1>
                    </div>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                 {/* Left Panel: Upload & Config */}
                 <div className="lg:col-span-2 space-y-10">
                     {/* Metadata Card */}
                     <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                         <div className="space-y-4">
                            <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Cycle Identity</h4>
                            <input 
                                type="text"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                placeholder="Quantum Research Team Vetting - Q1"
                                className="w-full text-3xl font-black italic text-zinc-900 placeholder:text-gray-100 focus:outline-none focus:placeholder:text-gray-50 transition-all border-b border-gray-50 pb-4"
                            />
                         </div>

                         <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                             <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Target Mission (Optional)</h4>
                                <select 
                                    value={selectedJob}
                                    onChange={(e) => setSelectedJob(e.target.value)}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl p-4 text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                >
                                    <option value="">Cold Pool (No Job Reference)</option>
                                    {jobs.map(j => <option key={j.id} value={j.id}>{j.title}</option>)}
                                </select>
                             </div>
                             <div className="space-y-4">
                                <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">Education Constraints</h4>
                                <select 
                                    value={criteria.educationLevel}
                                    onChange={(e) => setCriteria({ ...criteria, educationLevel: e.target.value })}
                                    className="w-full bg-gray-50 border border-gray-100 rounded-2xl p-4 text-sm font-bold focus:ring-4 focus:ring-secondary/5 outline-none transition-all"
                                >
                                    <option>High School</option>
                                    <option>Bachelor's</option>
                                    <option>Master's</option>
                                    <option>PhD</option>
                                </select>
                             </div>
                         </div>
                     </section>

                      {/* Selection Mode Switcher */}
                      <div className="flex bg-white/50 p-2 rounded-[32px] border border-gray-100/50 backdrop-blur-md mb-10">
                          <button 
                            type="button"
                            onClick={() => setScreeningMode('bulk')}
                            className={`flex-1 flex items-center justify-center space-x-3 py-4 rounded-[24px] font-black uppercase text-[10px] tracking-widest italic transition-all ${
                                screeningMode === 'bulk' ? 'bg-zinc-900 text-white shadow-xl' : 'text-gray-400 hover:text-zinc-900'
                            }`}
                          >
                              <Upload className="w-4 h-4" />
                              <span>Manual Matrix Upload</span>
                          </button>
                          <button 
                            type="button"
                            onClick={() => {
                                if (!selectedJob) {
                                    alert("Please reference a specific job to enable Neural Sync.");
                                    return;
                                }
                                setScreeningMode('job');
                            }}
                            className={`flex-1 flex items-center justify-center space-x-3 py-4 rounded-[24px] font-black uppercase text-[10px] tracking-widest italic transition-all ${
                                screeningMode === 'job' ? 'bg-zinc-900 text-white shadow-xl' : 'text-gray-400 hover:text-zinc-900'
                            }`}
                          >
                              <Database className="w-4 h-4" />
                              <span>Neural Sync (Job Pool)</span>
                          </button>
                      </div>

                      {/* Bulk Resume Matrix Dropzone OR Applicant Sync */}
                      {screeningMode === 'bulk' ? (
                          <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10">
                               <div className="flex items-center justify-between">
                                    <h3 className="text-xl font-black text-zinc-900 italic uppercase">Resume Reservoir</h3>
                                    <span className="text-[10px] font-black text-secondary italic uppercase tracking-widest">{files.length}/50 Metrics</span>
                               </div>

                               <div className="relative group">
                                   <input 
                                       type="file" 
                                       multiple 
                                       accept=".pdf"
                                       onChange={handleFileChange}
                                       className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                                   />
                                   <div className="border-4 border-dashed border-gray-100 rounded-[40px] p-16 flex flex-col items-center justify-center text-center space-y-6 group-hover:border-secondary/20 group-hover:bg-gray-50/50 transition-all">
                                       <div className="p-6 bg-gray-50 rounded-full text-gray-300 group-hover:bg-white group-hover:text-secondary group-hover:scale-110 transition-all shadow-sm">
                                           <Upload className="w-10 h-10" />
                                       </div>
                                       <div>
                                           <h4 className="text-xl font-black text-zinc-900 italic tracking-tight">Extract Raw Metrics</h4>
                                           <p className="text-xs text-gray-400 font-bold max-w-sm italic">Drag up to 50 PDF files directly into the neural cloud for vetting.</p>
                                       </div>
                                   </div>
                               </div>

                               {files.length > 0 && (
                                   <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                                       <AnimatePresence>
                                           {files.map((file, i) => (
                                               <motion.div 
                                                   key={`${file.name}-${i}`}
                                                   initial={{ opacity: 0, scale: 0.9 }}
                                                   animate={{ opacity: 1, scale: 1 }}
                                                   exit={{ opacity: 0, scale: 0.9 }}
                                                   className="bg-gray-50 border border-gray-100 rounded-2xl p-4 flex items-center justify-between group"
                                               >
                                                   <div className="flex items-center space-x-3 overflow-hidden">
                                                       <div className="p-2 bg-white rounded-lg text-gray-400">
                                                           <FileText className="w-4 h-4" />
                                                       </div>
                                                       <span className="text-[10px] font-black text-zinc-900 truncate italic">{file.name}</span>
                                                   </div>
                                                   <button onClick={() => removeFile(i)} className="p-1 hover:text-red-500 transition-colors">
                                                       <X className="w-4 h-4" />
                                                   </button>
                                               </motion.div>
                                           ))}
                                       </AnimatePresence>
                                   </div>
                               )}
                          </section>
                      ) : (
                          <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10">
                              <div className="flex items-center justify-between">
                                  <div className="space-y-1">
                                      <h3 className="text-xl font-black text-zinc-900 italic uppercase">Applicant Selection Matrix</h3>
                                      <p className="text-[8px] font-black text-gray-400 uppercase tracking-[0.2em] italic">Synchronizing existing job metadata for vetting</p>
                                  </div>
                                  <div className="flex items-center space-x-3">
                                      <div className="px-5 py-2 bg-gray-50 border border-gray-100 rounded-full text-[10px] font-black italic text-zinc-900">
                                          {selectedApplicants.size} / {applicants.length} Selected
                                      </div>
                                  </div>
                              </div>

                              {applicants.length === 0 ? (
                                  <div className="py-20 text-center space-y-6">
                                      <Users className="w-10 h-10 text-gray-200 mx-auto" />
                                      <p className="text-xs font-black text-gray-400 italic">No applicants found for this mission. Toggle Manual Matrix Upload instead.</p>
                                  </div>
                              ) : (
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                      {applicants.map((a) => {
                                          const resume = Array.isArray(a.resumes) ? a.resumes[0] : a.resumes;
                                          const isSelected = selectedApplicants.has(a.id);
                                          const hasResume = !!resume?.file_url;

                                          return (
                                              <motion.div 
                                                key={a.id}
                                                whileHover={{ scale: 1.02 }}
                                                onClick={() => hasResume && toggleApplicant(a.id)}
                                                className={`relative overflow-hidden cursor-pointer border-2 rounded-3xl p-6 transition-all space-y-4 ${
                                                    !hasResume ? 'opacity-50 grayscale cursor-not-allowed border-gray-50' :
                                                    isSelected ? 'border-primary bg-primary/5 shadow-2xl shadow-primary/10' : 'border-gray-100 hover:border-gray-200 bg-white'
                                                }`}
                                              >
                                                  <div className="flex items-center justify-between">
                                                      <div className="flex items-center space-x-3">
                                                          {a.profiles?.avatar_url ? (
                                                              <img src={a.profiles.avatar_url} className="w-8 h-8 rounded-xl object-cover" />
                                                          ) : (
                                                              <div className="w-8 h-8 bg-zinc-900 rounded-xl flex items-center justify-center text-[10px] text-white font-black italic uppercase">
                                                                  {a.profiles?.full_name[0]}
                                                              </div>
                                                          )}
                                                          <div className="overflow-hidden">
                                                              <h4 className="text-[10px] font-black text-zinc-900 truncate italic">{a.profiles?.full_name}</h4>
                                                              <p className="text-[8px] font-bold text-gray-400 truncate">{a.profiles?.headline || "Candidate Pool"}</p>
                                                          </div>
                                                      </div>
                                                      <div className={`p-2 rounded-xl transition-all ${isSelected ? "bg-primary text-white" : "bg-gray-50 text-gray-300"}`}>
                                                          {isSelected ? <CheckCircle2 className="w-3 h-3" /> : <MousePointer2 className="w-3 h-3" />}
                                                      </div>
                                                  </div>
                                                  
                                                  <div className="flex items-center justify-between pt-2">
                                                      <div className="flex items-center space-x-2">
                                                          <div className={`w-1.5 h-1.5 rounded-full ${hasResume ? 'bg-emerald-500' : 'bg-red-500'}`} />
                                                          <span className="text-[8px] font-black uppercase tracking-widest text-gray-400 italic">
                                                              {hasResume ? "Neural Vector Ready" : "Missing Metadata"}
                                                          </span>
                                                      </div>
                                                  </div>
                                              </motion.div>
                                          );
                                      })}
                                  </div>
                              )}
                          </section>
                      )}


                      {/* Question Config (Only if job selected) */}
                      <AnimatePresence>
                          {selectedJob && jobQuestions.length > 0 && (
                              <motion.section 
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-10 overflow-hidden"
                              >
                                  <div className="flex items-center space-x-3">
                                      <MessageSquare className="w-6 h-6 text-secondary" />
                                      <h3 className="text-xl font-black text-zinc-900 italic uppercase tracking-tight">Question Resonance Tuning</h3>
                                  </div>

                                  <div className="space-y-8">
                                      {jobQuestions.map((q) => (
                                          <div key={q.id} className="space-y-4 p-6 bg-gray-50 rounded-3xl border border-gray-100/50">
                                              <div className="flex justify-between items-start">
                                                  <p className="text-xs font-black text-zinc-900 italic max-w-md">{q.question}</p>
                                                  <span className="text-[8px] font-black uppercase tracking-widest text-gray-400 bg-white px-3 py-1 rounded-full border border-gray-100">{q.input_type}</span>
                                              </div>
                                              
                                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                                  {['yes_no', 'multiple_choice'].includes(q.input_type) ? (
                                                      <div className="space-y-2">
                                                          <h5 className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic px-1">Ideal Persistence Value</h5>
                                                          <select 
                                                            value={questionsConfig[q.question]?.value || ""}
                                                            onChange={(e) => setQuestionsConfig({
                                                                ...questionsConfig,
                                                                [q.question]: { ...questionsConfig[q.question], value: e.target.value }
                                                            })}
                                                            className="w-full bg-white border border-gray-100 rounded-xl p-3 text-[10px] font-bold focus:ring-4 focus:ring-secondary/5 outline-none"
                                                          >
                                                              <option value="">No Preference</option>
                                                              {q.input_type === 'yes_no' ? (
                                                                  <>
                                                                    <option value="yes">Yes / True</option>
                                                                    <option value="no">No / False</option>
                                                                  </>
                                                              ) : (
                                                                  q.options?.map((opt: string) => (
                                                                      <option key={opt} value={opt}>{opt}</option>
                                                                  ))
                                                              )}
                                                          </select>
                                                      </div>
                                                  ) : (
                                                      <div className="space-y-2 lg:col-span-2">
                                                          <h5 className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic px-1">Critical Response Keywords</h5>
                                                          <input 
                                                            type="text"
                                                            placeholder="Comma separated: Leadership, Scalability, P&L..."
                                                            value={questionsConfig[q.question]?.keywords || ""}
                                                            onChange={(e) => setQuestionsConfig({
                                                                ...questionsConfig,
                                                                [q.question]: { ...questionsConfig[q.question], keywords: e.target.value }
                                                            })}
                                                            className="w-full bg-white border border-gray-100 rounded-xl p-3 text-[10px] font-bold focus:ring-4 focus:ring-secondary/5 outline-none"
                                                          />
                                                      </div>
                                                  )}
                                              </div>
                                          </div>
                                      ))}
                                  </div>
                              </motion.section>
                          )}
                      </AnimatePresence>

                      {/* Criteria Config */}
                      <section className="bg-zinc-900 rounded-[48px] p-12 shadow-2xl space-y-10">
                        <div className="flex items-center space-x-3">
                            <Target className="w-6 h-6 text-secondary" />
                            <h3 className="text-2xl font-black text-white italic tracking-tight uppercase">Target Constraints</h3>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Critical Skills</h5>
                                    <textarea 
                                        rows={3}
                                        value={criteria.requiredSkills}
                                        onChange={(e) => setCriteria({...criteria, requiredSkills: e.target.value})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-sm font-bold italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                        placeholder="Comma separated: Python, React, AWS..."
                                    />
                                </div>
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Experience (Years)</h5>
                                    <input 
                                        type="number"
                                        value={criteria.minExperience ?? ""}
                                        onChange={(e) => {
                                            const val = parseInt(e.target.value);
                                            setCriteria({...criteria, minExperience: isNaN(val) ? 0 : val});
                                        }}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-3xl font-black italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                    />
                                </div>
                            </div>

                            <div className="space-y-8">
                                <div className="space-y-4">
                                    <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Neural Keywords</h5>
                                    <textarea 
                                        rows={8}
                                        value={criteria.keywords}
                                        onChange={(e) => setCriteria({...criteria, keywords: e.target.value})}
                                        className="w-full bg-white/5 border border-white/10 rounded-2xl p-6 text-white text-sm font-bold italic focus:ring-4 focus:ring-secondary/20 outline-none"
                                        placeholder="Keywords to boost matching: Startup, Scale-up, Leadership, High Performance..."
                                    />
                                </div>
                            </div>
                        </div>
                     </section>
                 </div>

                 {/* Right Panel: Weighting & Action */}
                 <div className="space-y-8">
                    <div className="sticky top-8 space-y-8">
                         {/* Weighted Scoring Controller */}
                         <section className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-xl space-y-10">
                            <div className="flex items-center space-x-3">
                                <SlidersHorizontal className="w-5 h-5 text-primary" />
                                <h3 className="text-xl font-black text-zinc-900 italic uppercase">Weighted Logic</h3>
                            </div>

                            <div className="space-y-8">
                                {[
                                    { key: "skills", label: "Skills Density", val: weights.skills, color: "accent-primary" },
                                    { key: "experience", label: "Experience Tenure", val: weights.experience, color: "accent-secondary" },
                                    { key: "education", label: "Academic Sync", val: weights.education, color: "accent-zinc-900" },
                                    { key: "keywords", label: "Keyword Hitrate", val: weights.keywords, color: "accent-emerald-500" },
                                    { key: "questions", label: "Question Resonance", val: weights.questions, color: "accent-amber-500" },
                                    { key: "assessments", label: "Assessment Sync", val: weights.assessments, color: "accent-purple-500" }
                                ].map((w) => (
                                    <div key={w.key} className="space-y-3">
                                        <div className="flex justify-between items-center px-1">
                                            <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic">{w.label}</span>
                                            <span className="text-xs font-black text-zinc-900 italic">{w.val}%</span>
                                        </div>
                                        <input 
                                            type="range"
                                            min="0"
                                            max="100"
                                            value={w.val}
                                            onChange={(e) => setWeights({ ...weights, [w.key]: parseInt(e.target.value) })}
                                            className={`w-full h-1.5 bg-gray-100 rounded-full appearance-none cursor-pointer ${w.color}`}
                                        />
                                    </div>
                                ))}
                            </div>

                            <div className="p-6 bg-gray-50 rounded-3xl space-y-2">
                                <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic text-center">Neural Configuration Status</p>
                                <div className="text-center font-black italic text-xl">
                                    {Object.values(weights).reduce((a, b) => a + b, 0) === 100 ? (
                                        <span className="text-emerald-500">OPTIMAL (100%)</span>
                                    ) : (
                                        <span className="text-amber-500 text-sm italic">UNSTABLE ({Object.values(weights).reduce((a, b) => a + b, 0)}%)</span>
                                    )}
                                </div>
                            </div>
                         </section>

                         {/* Action Buttons */}
                         <div className="space-y-4">
                            <button 
                                onClick={startScreening}
                                disabled={uploading || processing || files.length === 0 || !title}
                                className="w-full py-6 bg-zinc-900 text-white rounded-[32px] font-black text-lg uppercase tracking-widest italic shadow-2xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:grayscale group relative overflow-hidden"
                            >
                                <div className="relative z-10 flex items-center justify-center space-x-3">
                                    {(uploading || processing) ? (
                                        <Loader2 className="w-6 h-6 animate-spin" />
                                    ) : (
                                        <Zap className="w-6 h-6 text-primary group-hover:scale-125 transition-transform" />
                                    )}
                                    <span>Initiate Vetting Cycle</span>
                                </div>
                                <div className="absolute inset-0 bg-primary/20 translate-x-[-100%] group-hover:translate-x-0 transition-transform duration-700" />
                            </button>

                            <button className="w-full py-5 border-2 border-gray-100 text-gray-400 rounded-[32px] font-black text-xs uppercase tracking-widest italic hover:bg-gray-50 transition-all">
                                Save Simulation Template
                            </button>
                         </div>
                    </div>
                 </div>
            </div>

            {/* Overlays */}
            <AnimatePresence>
                {(uploading || processing) && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-zinc-900/90 z-50 flex items-center justify-center p-6 backdrop-blur-xl"
                    >
                        <div className="max-w-md w-full space-y-12 text-center text-white">
                             <div className="relative">
                                 <motion.div 
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                    className="w-48 h-48 border-4 border-white/5 border-t-secondary rounded-full mx-auto"
                                 />
                                 <BrainCircuit className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-16 h-16 text-white animate-pulse" />
                             </div>

                             <div className="space-y-4">
                                <h3 className="text-4xl font-black italic tracking-tighter uppercase">
                                    {uploading ? "Deploying Metrics..." : "Computing Intelligence..."}
                                </h3>
                                <p className="text-gray-400 font-bold italic">
                                    {uploading ? "Transmitting files to neural cloud storage." : "AI is analyzing resume matrices against constraints."}
                                </p>
                             </div>

                             <div className="space-y-4">
                                 <div className="flex justify-between items-end text-[10px] font-black uppercase tracking-widest text-secondary">
                                     <span>Vector Progress</span>
                                     <span>{progress}%</span>
                                 </div>
                                 <div className="w-full h-3 bg-white/10 rounded-full overflow-hidden border border-white/5">
                                     <motion.div 
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        className="h-full bg-secondary shadow-[0_0_20px_rgba(255,102,0,0.8)]"
                                     />
                                 </div>
                                 <div className="flex justify-between text-[10px] font-black uppercase tracking-widest text-gray-500">
                                     <span>Batch processing active</span>
                                     <span>Metric Stream {Math.ceil(progress * files.length / 100)} / {files.length}</span>
                                 </div>
                             </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
