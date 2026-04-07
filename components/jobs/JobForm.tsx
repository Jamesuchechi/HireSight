"use client";

import { useState } from "react";
import { useForm, Controller, SubmitHandler, FieldValues, UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { 
  ChevronRight, ChevronLeft, Rocket, CheckCircle, 
  MapPin, Briefcase, DollarSign, BrainCircuit, Type, FileText, Users, Calendar, Star 
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import RichTextEditor from "./RichTextEditor";
import SkillsInput from "./SkillsInput";
import ScreeningQuestionsInput from "./ScreeningQuestionsInput";

interface Skill {
  name: string;
  is_required: boolean;
}

interface ScreeningQuestion {
  id: string;
  question: string;
  input_type: "short_text" | "long_text" | "yes_no" | "multiple_choice";
  options?: string[];
  is_required: boolean;
}

interface JobFormValues extends FieldValues {
  title: string;
  location: string;
  remote_type: "remote" | "hybrid" | "onsite";
  experience_level: "entry" | "mid" | "senior" | "lead" | "executive";
  job_type: "full-time" | "part-time" | "contract" | "internship";
  salary_min: number;
  salary_max: number;
  salary_period: "hourly" | "monthly" | "yearly";
  currency: string;
  department: string;
  description: string;
  responsibilities: string;
  nice_to_have: string;
  benefits: string;
  requirements: string;
  positions_available: number;
  application_deadline: string;
  requires_cover_letter: boolean;
  requires_portfolio: boolean;
  is_featured: boolean;
  status: "draft" | "active";
  skills: Skill[];
  screening_questions: ScreeningQuestion[];
}

const jobSchema = z.object({
  title: z.string().min(5, "Title must be at least 5 characters"),
  location: z.string().min(2, "Location is required"),
  remote_type: z.enum(["remote", "hybrid", "onsite"]),
  experience_level: z.enum(["entry", "mid", "senior", "lead", "executive"]),
  job_type: z.enum(["full-time", "part-time", "contract", "internship"]),
  salary_min: z.number().default(0),
  salary_max: z.number().default(0),
  salary_period: z.enum(["hourly", "monthly", "yearly"]).default("yearly"),
  currency: z.string().default("USD"),
  department: z.string().default(""),
  description: z.string().min(50, "Description must be at least 50 characters"),
  responsibilities: z.string().default(""),
  nice_to_have: z.string().default(""),
  benefits: z.string().default(""),
  requirements: z.string().default(""),
  positions_available: z.number().min(1).default(1),
  application_deadline: z.string().optional(),
  requires_cover_letter: z.boolean().default(false),
  requires_portfolio: z.boolean().default(false),
  is_featured: z.boolean().default(false),
  status: z.enum(["draft", "active"]).default("active"),
  skills: z.array(z.object({
    name: z.string(),
    is_required: z.boolean()
  })),
  screening_questions: z.array(z.object({
    id: z.string(),
    question: z.string(),
    input_type: z.enum(["short_text", "long_text", "yes_no", "multiple_choice"]),
    options: z.array(z.string()).optional(),
    is_required: z.boolean()
  }))
});

export default function JobForm() {
  const router = useRouter();
  const supabase = createClient();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form: UseFormReturn<JobFormValues> = useForm<JobFormValues>({
    resolver: zodResolver(jobSchema) as any,
    defaultValues: {
      title: "",
      location: "",
      remote_type: "remote",
      experience_level: "mid",
      job_type: "full-time",
      salary_min: 0,
      salary_max: 0,
      salary_period: "yearly",
      currency: "USD",
      department: "",
      description: "",
      responsibilities: "",
      nice_to_have: "",
      benefits: "",
      requirements: "",
      positions_available: 1,
      application_deadline: "",
      requires_cover_letter: false,
      requires_portfolio: false,
      is_featured: false,
      status: "active",
      skills: [],
      screening_questions: []
    } as any
  });

  const { register, control, handleSubmit, formState: { errors }, watch, trigger } = form as any;

  const nextStep = async () => {
    const fieldsToValidate = step === 1 
      ? ["title", "department", "location", "remote_type", "experience_level", "job_type", "salary_min", "salary_max", "salary_period"] 
      : step === 2 
      ? ["description", "responsibilities", "nice_to_have", "benefits"] 
      : step === 3
      ? ["skills", "positions_available", "application_deadline"]
      : [];
    
    const isValid = await trigger(fieldsToValidate as any);
    if (isValid) setStep(prev => prev + 1);
  };

  const prevStep = () => setStep(prev => prev - 1);

  const onSubmit: SubmitHandler<JobFormValues> = async (values) => {
    setIsSubmitting(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not authenticated");

      // 1. Insert Job
      const { data: jobData, error: jobError } = await supabase
        .from("jobs")
        .insert({
          company_id: user.id,
          title: values.title,
          description: values.description,
          requirements: values.requirements,
          salary_min: values.salary_min,
          salary_max: values.salary_max,
          salary_period: values.salary_period,
          currency: values.currency,
          department: values.department,
          location: values.location,
          remote_type: values.remote_type,
          experience_level: values.experience_level,
          job_type: values.job_type,
          status: values.status,
          responsibilities: values.responsibilities,
          nice_to_have: values.nice_to_have,
          benefits: values.benefits,
          positions_available: values.positions_available,
          application_deadline: values.application_deadline || null,
          requires_cover_letter: values.requires_cover_letter,
          requires_portfolio: values.requires_portfolio,
          is_featured: values.is_featured,
        })
        .select()
        .single();

      const job = jobData as { id: string };

      if (jobError) throw jobError;

      // 2. Insert Skills
      if (values.skills.length > 0) {
        const { error: skillsError } = await supabase
          .from("job_skills")
          .insert(values.skills.map(s => ({
            job_id: job.id,
            skill_name: s.name,
            is_required: s.is_required
          })));
        if (skillsError) throw skillsError;
      }

      // 3. Insert Screening Questions
      if (values.screening_questions.length > 0) {
        const { error: questionsError } = await supabase
          .from("job_screening_questions")
          .insert(values.screening_questions.map((q, idx) => ({
            job_id: job.id,
            question: q.question,
            input_type: q.input_type,
            options: q.options,
            is_required: q.is_required,
            order_index: idx
          })));
        if (questionsError) throw questionsError;
      }

      router.push("/dashboard/jobs");
    } catch (error) {
      console.error("Error creating job:", error);
      alert("Failed to create job. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const stepTitles = ["Protocol Origin", "Core Logic", "Mission Setup", "Screening Phase"];
  const stepIcons = [<Rocket key="1" />, <Type key="2" />, <FileText key="3" />, <BrainCircuit key="4" />];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Stepper */}
      <div className="flex items-center justify-between mb-12 bg-white p-6 rounded-[40px] border border-gray-100 shadow-sm">
        {stepTitles.map((title, i) => (
          <div key={i} className="flex-1 flex flex-col items-center relative gap-2">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-500 z-10 ${
                step > i + 1 ? "bg-emerald-500 text-white" : 
                step === i + 1 ? "bg-primary text-white shadow-xl shadow-primary/20 scale-110" : 
                "bg-gray-100 text-gray-400"
            }`}>
              {step > i + 1 ? <CheckCircle className="w-6 h-6" /> : stepIcons[i]}
            </div>
            <span className={`text-[10px] font-black uppercase tracking-widest ${
                step === i + 1 ? "text-primary" : "text-gray-400"
            }`}>
                {title}
            </span>
            {i < 3 && (
              <div className="absolute left-[calc(50%+30px)] top-6 w-[calc(100%-60px)] h-0.5 bg-gray-50">
                <motion.div 
                  className="h-full bg-primary"
                  initial={{ width: 0 }}
                  animate={{ width: step > i + 1 ? "100%" : "0%" }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-10">
        <AnimatePresence mode="wait">
          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8"
            >
              <div className="space-y-2">
                <h2 className="text-3xl font-black font-display italic text-zinc-900 tracking-tighter">Job Configuration</h2>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic">Initialize the basic parameters for the position</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-2 md:col-span-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Position Title</label>
                  <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                    <div className="p-4 flex items-center justify-center text-primary border-r border-gray-100">
                      <Briefcase className="w-5 h-5" />
                    </div>
                    <input
                      {...register("title")}
                      placeholder="e.g. Senior Backend Engineer"
                      className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                    />
                  </div>
                  {errors.title && <p className="text-rose-500 text-[10px] uppercase font-black tracking-widest pl-4">{errors.title.message}</p>}
                </div>

                <div className="space-y-2 md:col-span-1">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Department</label>
                  <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                    <div className="p-4 flex items-center justify-center text-primary border-r border-gray-100">
                      <Users className="w-5 h-5" />
                    </div>
                    <input
                      {...register("department")}
                      placeholder="e.g. Engineering"
                      className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Work Location</label>
                  <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                    <div className="p-4 flex items-center justify-center text-primary border-r border-gray-100">
                      <MapPin className="w-5 h-5" />
                    </div>
                    <input
                      {...register("location")}
                      placeholder="e.g. San Francisco, CA"
                      className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Work Protocol</label>
                  <select
                    {...register("remote_type")}
                    className="w-full bg-gray-50/50 border border-gray-100 rounded-[24px] p-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all appearance-none cursor-pointer"
                  >
                    <option value="remote">Fully Remote</option>
                    <option value="hybrid">Hybrid Infrastructure</option>
                    <option value="onsite">On-Site Only</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Experience Scalar</label>
                  <select
                    {...register("experience_level")}
                    className="w-full bg-gray-50/50 border border-gray-100 rounded-[24px] p-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all appearance-none cursor-pointer"
                  >
                    <option value="entry">Entry Level</option>
                    <option value="mid">Mid-Senior</option>
                    <option value="senior">Senior Level</option>
                    <option value="lead">Lead Architect</option>
                    <option value="executive">Executive Management</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Employment Model</label>
                   <select
                    {...register("job_type")}
                    className="w-full bg-gray-50/50 border border-gray-100 rounded-[24px] p-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all appearance-none cursor-pointer"
                  >
                    <option value="full-time">Full-Time (Direct)</option>
                    <option value="part-time">Part-Time (Direct)</option>
                    <option value="contract">Contract (Remote/Onsite)</option>
                    <option value="internship">Academic Internship</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Minimum Compensation</label>
                  <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                    <div className="p-4 flex items-center justify-center text-emerald-500 border-r border-gray-100">
                      <DollarSign className="w-5 h-5" />
                    </div>
                    <input
                      type="number"
                      {...register("salary_min", { valueAsNumber: true })}
                      placeholder="e.g. 120000"
                      className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Maximum Compensation</label>
                   <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                    <div className="p-4 flex items-center justify-center text-emerald-500 border-r border-gray-100">
                      <DollarSign className="w-5 h-5" />
                    </div>
                    <input
                      type="number"
                      {...register("salary_max", { valueAsNumber: true })}
                      placeholder="e.g. 180000"
                      className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8"
            >
              <div className="space-y-2">
                <h2 className="text-3xl font-black font-display italic text-zinc-900 tracking-tighter">Manifesto Building</h2>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic">Define the detailed scope and requirements</p>
              </div>

              <div className="space-y-10">
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 ml-4">
                      <FileText className="w-4 h-4 text-primary" />
                      <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 italic">Job Description & Protocol</label>
                  </div>
                  <Controller
                    name="description"
                    control={control}
                    render={({ field }) => (
                      <RichTextEditor 
                        content={field.value} 
                        onChange={field.onChange} 
                        placeholder="Detail the challenges, mission, and day-to-day operations..."
                      />
                    )}
                  />
                  {errors.description && <p className="text-rose-500 text-[10px] uppercase font-black tracking-widest pl-4">{errors.description.message}</p>}
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-2 ml-4">
                      <Briefcase className="w-4 h-4 text-primary" />
                      <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 italic">Key Responsibilities</label>
                  </div>
                  <Controller
                    name="responsibilities"
                    control={control}
                    render={({ field }) => (
                      <RichTextEditor 
                        content={field.value} 
                        onChange={field.onChange} 
                        placeholder="Outline the primary duties and expected outcomes..."
                      />
                    )}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-2 ml-4">
                      <BrainCircuit className="w-4 h-4 text-primary" />
                      <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 italic">Nice to Have / Bonus Protocol</label>
                  </div>
                  <Controller
                    name="nice_to_have"
                    control={control}
                    render={({ field }) => (
                      <RichTextEditor 
                        content={field.value} 
                        onChange={field.onChange} 
                        placeholder="Additional skills or experience that would be an advantage..."
                      />
                    )}
                  />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center space-x-2 ml-4">
                      <DollarSign className="w-4 h-4 text-emerald-500" />
                      <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 italic">Benefits & Perks</label>
                  </div>
                  <Controller
                    name="benefits"
                    control={control}
                    render={({ field }) => (
                      <RichTextEditor 
                        content={field.value} 
                        onChange={field.onChange} 
                        placeholder="Detail the compensation, equity, and other perks..."
                      />
                    )}
                  />
                </div>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-10"
            >
              <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                <div className="space-y-2">
                  <h2 className="text-3xl font-black font-display italic text-zinc-900 tracking-tighter">Skill Matrix</h2>
                  <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic">Tag the specific competencies required for the mission</p>
                </div>
                <Controller
                  name="skills"
                  control={control}
                  render={({ field }) => (
                    <SkillsInput value={field.value} onChange={field.onChange} />
                  )}
                />
              </div>

              <div className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8">
                <div className="space-y-2">
                  <h2 className="text-3xl font-black font-display italic text-zinc-900 tracking-tighter">Mission Strategy</h2>
                  <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic">Configure deployment parameters and requirements</p>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Deployment Deadline</label>
                    <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                      <div className="p-4 flex items-center justify-center text-primary border-r border-gray-100">
                        <Calendar className="w-5 h-5" />
                      </div>
                      <input
                        type="date"
                        {...register("application_deadline")}
                        className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 ml-4 italic">Positions Available</label>
                    <div className="flex bg-gray-50/50 border border-gray-100 rounded-[24px] overflow-hidden focus-within:ring-4 focus-within:ring-primary/5 transition-all">
                      <div className="p-4 flex items-center justify-center text-primary border-r border-gray-100">
                        <Users className="w-5 h-5" />
                      </div>
                      <input
                        type="number"
                        {...register("positions_available", { valueAsNumber: true })}
                        className="w-full bg-transparent p-4 text-sm font-bold focus:outline-none"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-6 pt-4">
                  <div className="flex items-center justify-between p-6 bg-gray-50/50 rounded-[32px] border border-gray-100">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-primary/10 text-primary rounded-2xl">
                        <Star className="w-5 h-5" />
                      </div>
                      <div>
                        <p className="text-sm font-black text-zinc-900 italic">Premium Highlight</p>
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Feature this job at the top of the search results</p>
                      </div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" {...register("is_featured")} className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                    </label>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <label className="flex items-center space-x-3 p-6 bg-white border border-gray-100 rounded-[32px] cursor-pointer hover:border-primary/20 transition-all">
                      <input type="checkbox" {...register("requires_cover_letter")} className="w-5 h-5 rounded-lg border-gray-300 text-primary focus:ring-primary" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-900 italic">Require Cover Letter</span>
                    </label>
                    <label className="flex items-center space-x-3 p-6 bg-white border border-gray-100 rounded-[32px] cursor-pointer hover:border-primary/20 transition-all">
                      <input type="checkbox" {...register("requires_portfolio")} className="w-5 h-5 rounded-lg border-gray-300 text-primary focus:ring-primary" />
                      <span className="text-[10px] font-black uppercase tracking-widest text-zinc-900 italic">Require Portfolio URL</span>
                    </label>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {step === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white border border-gray-100 rounded-[48px] p-10 shadow-sm space-y-8"
            >
              <div className="space-y-2">
                <h2 className="text-3xl font-black font-display italic text-zinc-900 tracking-tighter">Applicant Screening</h2>
                <p className="text-xs text-gray-400 font-bold uppercase tracking-widest italic">Configure logic to automate the initial vetting process</p>
              </div>
              <Controller
                name="screening_questions"
                control={control}
                render={({ field }) => (
                  <ScreeningQuestionsInput value={field.value} onChange={field.onChange} />
                )}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Form Actions */}
        <div className="flex items-center justify-between pt-6">
          {step > 1 ? (
            <button
              type="button"
              onClick={prevStep}
              className="px-8 py-4 bg-white border border-gray-100 rounded-2xl font-black text-xs uppercase tracking-widest text-gray-400 hover:text-zinc-900 hover:bg-gray-50 transition-all flex items-center space-x-2"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous Phase</span>
            </button>
          ) : <div />}

          {step < 4 ? (
            <button
              type="button"
              onClick={nextStep}
              className="px-10 py-4 bg-zinc-900 text-white rounded-2xl font-black text-xs uppercase tracking-widest italic shadow-xl hover:scale-[1.05] active:scale-[0.95] transition-all flex items-center space-x-2"
            >
              <span>Continue Protocol</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-12 py-4 bg-primary text-white rounded-[24px] font-black text-sm uppercase tracking-widest italic shadow-2xl transition-all flex items-center space-x-3 ${
                  isSubmitting ? "opacity-50 cursor-not-allowed scale-95" : "hover:scale-[1.05] active:scale-[0.95]"
              }`}
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
          )}
        </div>
      </form>
    </div>
  );
}
