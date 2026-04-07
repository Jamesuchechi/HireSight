"use client";

import { useState, KeyboardEvent } from "react";
import { X, Plus, BrainCircuit } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Skill {
  name: string;
  is_required: boolean;
}

interface SkillsInputProps {
  value: Skill[];
  onChange: (skills: Skill[]) => void;
}

export default function SkillsInput({ value, onChange }: SkillsInputProps) {
  const [inputValue, setInputValue] = useState("");

  const addSkill = () => {
    const trimmed = inputValue.trim();
    if (trimmed && !value.some(s => s.name.toLowerCase() === trimmed.toLowerCase())) {
      onChange([...value, { name: trimmed, is_required: true }]);
      setInputValue("");
    }
  };

  const removeSkill = (name: string) => {
    onChange(value.filter(s => s.name !== name));
  };

  const toggleRequired = (name: string) => {
    onChange(value.map(s => s.name === name ? { ...s, is_required: !s.is_required } : s));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addSkill();
    }
  };

  return (
    <div className="space-y-4">
      <div className="relative group/input">
        <div className="absolute left-5 top-1/2 -translate-y-1/2 p-2 bg-primary/10 text-primary rounded-xl transition-all group-focus-within/input:scale-110">
          <BrainCircuit className="w-4 h-4" />
        </div>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Add skills (e.g. React, Python, UI Design)..."
          className="w-full pl-14 pr-24 py-4 bg-white border border-gray-100 rounded-[24px] text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 transition-all shadow-sm"
        />
        <button
          type="button"
          onClick={addSkill}
          className="absolute right-3 top-1/2 -translate-y-1/2 px-4 py-2 bg-zinc-900 text-white text-[10px] font-black uppercase tracking-widest italic rounded-2xl hover:bg-primary transition-all"
        >
          Add Skill
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <AnimatePresence>
          {value.map((skill) => (
            <motion.div
              key={skill.name}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className={`group flex items-center space-x-2 px-4 py-2.5 rounded-[20px] border transition-all hover:shadow-lg ${
                skill.is_required 
                  ? "bg-primary/5 border-primary/20" 
                  : "bg-gray-50 border-gray-100"
              }`}
            >
              <button
                type="button"
                onClick={() => toggleRequired(skill.name)}
                className={`text-[10px] font-black uppercase tracking-widest select-none ${
                    skill.is_required ? "text-primary" : "text-gray-400 group-hover:text-gray-600"
                }`}
              >
                {skill.name} {skill.is_required ? "Required" : "Optional"}
              </button>
              
              <button
                type="button"
                onClick={() => removeSkill(skill.name)}
                className="p-1 hover:bg-white rounded-full transition-all group-hover:scale-110"
              >
                <X className={`w-3.5 h-3.5 ${skill.is_required ? "text-primary" : "text-gray-400"}`} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>

        {value.length === 0 && (
          <div className="w-full py-10 border-2 border-dashed border-gray-100 rounded-[32px] flex flex-col items-center justify-center text-gray-400">
             <Plus className="w-8 h-8 mb-2 opacity-30" />
             <p className="text-xs font-bold uppercase tracking-widest text-gray-300">Added skills will appear here</p>
          </div>
        )}
      </div>
    </div>
  );
}
