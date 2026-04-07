"use client";

import { useState } from "react";
import { useForm, Controller, SubmitHandler, FieldValues, UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { 
  ChevronRight, ChevronLeft, Rocket, CheckCircle, 
  MapPin, Briefcase, DollarSign, BrainCircuit, Type, FileText 
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
  currency: string;
  description: string;
  requirements: string;
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
  currency: z.string().default("USD"),
  description: z.string().min(50, "Description must be at least 50 characters"),
  requirements: z.string().default(""),
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
      currency: "USD",
      description: "",
      requirements: "",
      status: "active",
      skills: [],
      screening_questions: []
    } as any
  });

  const { register, control, handleSubmit, formState: { errors }, watch, trigger } = form as any;

  const nextStep = async () => {
    const fieldsToValidate = step === 1 
      ? ["title", "location", "remote_type", "experience_level", "job_type"] 
      : step === 2 
      ? ["description"] 
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
          currency: values.currency,
          location: values.location,
          remote_type: values.remote_type,
          experience_level: values.experience_level,
          job_type: values.job_type,
          status: values.status,
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

  const stepTitles = ["Protocol Origin", "Core Logic", "Screening Phase"];
  const stepIcons = [<Rocket key="1" />, <Type key="2" />, <BrainCircuit key="3" />];

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
            {i < 2 && (
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
                <div className="space-y-2 md:col-span-2">
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

              <div className="space-y-6">
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
              </div>
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

          {step < 3 ? (
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
