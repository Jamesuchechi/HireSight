"use client";

import { Plus, X, List, CheckSquare, Type, AlignLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ScreeningQuestion {
  id: string;
  question: string;
  input_type: 'short_text' | 'long_text' | 'yes_no' | 'multiple_choice';
  options?: string[];
  is_required: boolean;
}

interface ScreeningQuestionsInputProps {
  value: ScreeningQuestion[];
  onChange: (questions: ScreeningQuestion[]) => void;
}

export default function ScreeningQuestionsInput({ value, onChange }: ScreeningQuestionsInputProps) {
  const addQuestion = () => {
    const newQuestion: ScreeningQuestion = {
      id: Math.random().toString(36).substr(2, 9),
      question: "",
      input_type: "short_text",
      is_required: true,
    };
    onChange([...value, newQuestion]);
  };

  const removeQuestion = (id: string) => {
    onChange(value.filter(q => q.id !== id));
  };

  const updateQuestion = (id: string, updates: Partial<ScreeningQuestion>) => {
    onChange(value.map(q => q.id === id ? { ...q, ...updates } : q));
  };

  const addOption = (id: string) => {
    const question = value.find(q => q.id === id);
    if (question && question.input_type === "multiple_choice") {
      const options = question.options || [];
      updateQuestion(id, { options: [...options, ""] });
    }
  };

  const updateOption = (id: string, index: number, val: string) => {
    const question = value.find(q => q.id === id);
    if (question && question.options) {
      const options = [...question.options];
      options[index] = val;
      updateQuestion(id, { options });
    }
  };

  const removeOption = (id: string, index: number) => {
    const question = value.find(q => q.id === id);
    if (question && question.options) {
      updateQuestion(id, { options: question.options.filter((_, i) => i !== index) });
    }
  };

  return (
    <div className="space-y-6">
      <AnimatePresence>
        {value.map((q, index) => (
          <motion.div
            key={q.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="group relative bg-white border border-gray-100 rounded-[32px] p-8 shadow-sm hover:shadow-xl transition-all duration-500"
          >
            <div className="absolute -left-3 top-8 w-1 h-12 bg-primary rounded-full" />
            
            <div className="flex items-start justify-between mb-6">
               <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center font-black text-[10px] text-gray-400">
                    {index + 1}
                  </div>
                  <h4 className="text-sm font-black text-zinc-900 italic uppercase tracking-tight">Question Protocol</h4>
               </div>
               <button
                 type="button"
                 onClick={() => removeQuestion(q.id)}
                 className="p-2 hover:bg-rose-50 text-rose-400 rounded-xl transition-all"
               >
                 <X className="w-5 h-5" />
               </button>
            </div>

            <div className="space-y-6">
              <input
                type="text"
                value={q.question}
                onChange={(e) => updateQuestion(q.id, { question: e.target.value })}
                placeholder="Enter your screening question..."
                className="w-full bg-gray-50/50 border border-gray-100 rounded-2xl px-6 py-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="relative group/select">
                   <select
                     value={q.input_type}
                     onChange={(e) => updateQuestion(q.id, { 
                       input_type: e.target.value as ScreeningQuestion['input_type'],
                       options: e.target.value === 'multiple_choice' ? [""] : undefined
                     })}
                     className="w-full appearance-none bg-white border border-gray-100 rounded-2xl px-12 py-4 text-xs font-black uppercase tracking-widest text-gray-500 focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all cursor-pointer"
                   >
                     <option value="short_text">Short Text Response</option>
                     <option value="long_text">Long Text Response</option>
                     <option value="yes_no">Yes / No Switch</option>
                     <option value="multiple_choice">Multiple Choice</option>
                   </select>
                   <div className="absolute left-4 top-1/2 -translate-y-1/2 text-primary">
                      {q.input_type === 'short_text' && <Type className="w-4 h-4" />}
                      {q.input_type === 'long_text' && <AlignLeft className="w-4 h-4" />}
                      {q.input_type === 'yes_no' && <CheckSquare className="w-4 h-4" />}
                      {q.input_type === 'multiple_choice' && <List className="w-4 h-4" />}
                   </div>
                </div>

                <div className="flex items-center space-x-4 px-6 bg-gray-50/50 rounded-2xl border border-gray-100">
                   <label className="text-[10px] font-black uppercase tracking-widest text-gray-400 flex-1">Is Required</label>
                   <input
                     type="checkbox"
                     checked={q.is_required}
                     onChange={(e) => updateQuestion(q.id, { is_required: e.target.checked })}
                     className="w-5 h-5 rounded-lg border-gray-200 text-primary focus:ring-primary transition-all cursor-pointer"
                   />
                </div>
              </div>

              {q.input_type === 'multiple_choice' && (
                <div className="space-y-3 pt-4 pl-4 border-l-2 border-gray-50">
                   <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Options</p>
                   {q.options?.map((option, optIdx) => (
                     <div key={optIdx} className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-primary/20" />
                        <input
                          type="text"
                          value={option}
                          onChange={(e) => updateOption(q.id, optIdx, e.target.value)}
                          placeholder={`Option ${optIdx + 1}`}
                          className="flex-1 bg-white border border-gray-100 rounded-xl px-4 py-2 text-xs font-bold focus:outline-none focus:ring-2 focus:ring-primary/5"
                        />
                        <button
                          type="button"
                          onClick={() => removeOption(q.id, optIdx)}
                          className="p-2 text-gray-300 hover:text-rose-400 transition-colors"
                        >
                          <X className="w-4 h-4" />
                        </button>
                     </div>
                   ))}
                   <button
                     type="button"
                     onClick={() => addOption(q.id)}
                     className="text-[10px] font-black text-primary uppercase tracking-widest flex items-center space-x-1 hover:underline pt-2"
                   >
                     <Plus className="w-3 h-3" />
                     <span>Add Option</span>
                   </button>
                </div>
              )}
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      <button
        type="button"
        onClick={addQuestion}
        className="w-full py-6 border-2 border-dashed border-gray-100 rounded-[32px] flex items-center justify-center space-x-3 text-gray-400 hover:border-primary/20 hover:text-primary transition-all group"
      >
        <div className="p-2 bg-gray-50 rounded-xl group-hover:bg-primary/10 transition-colors">
            <Plus className="w-5 h-5" />
        </div>
        <span className="text-sm font-black uppercase tracking-widest italic">Add Screening Question</span>
      </button>

      {value.length === 0 && (
          <div className="bg-primary/5 rounded-[40px] p-8 text-center space-y-2">
              <p className="text-xs font-black text-primary uppercase tracking-widest">Optional: Protocol Enforcement</p>
              <p className="text-xs text-primary/60 font-bold max-w-sm mx-auto italic">Screening questions help your AI filter candidates before you even see their profile.</p>
          </div>
      )}
    </div>
  );
}
