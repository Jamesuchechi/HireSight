import { Briefcase } from "lucide-react";
import { Experience } from "@/types/profile";

interface ExperienceTimelineProps {
  experiences: Experience[];
}

export default function ExperienceTimeline({ experiences }: ExperienceTimelineProps) {
  if (!experiences || experiences.length === 0) {
    return (
      <div className="text-center py-10 bg-gray-50 rounded-[32px] border border-dashed border-gray-200">
        <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">No professional records found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h4 className="text-xl font-black text-zinc-900 italic uppercase tracking-tighter flex items-center space-x-3">
        <span className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center">
          <Briefcase className="w-4 h-4 text-primary" />
        </span>
        <span>Operative History</span>
      </h4>
      <div className="space-y-8 relative before:absolute before:left-7 before:top-10 before:bottom-0 before:w-px before:bg-gray-100">
        {experiences.map((exp, i) => (
          <div key={i} className="flex space-x-6 relative group">
            <div className={`w-14 h-14 shrink-0 rounded-2xl flex items-center justify-center border-2 transition-all ${
              exp.current ? 'bg-zinc-900 border-primary text-primary' : 'bg-gray-50 border-gray-100 text-gray-400'
            }`}>
              <Briefcase className="w-6 h-6" />
            </div>
            <div className="space-y-2 pt-1">
              <div className="flex flex-col md:flex-row md:items-center md:space-x-4">
                <h5 className="font-black text-zinc-900 italic text-lg leading-none">{exp.role}</h5>
                <span className="text-xs font-black text-primary uppercase tracking-widest bg-primary/10 px-2 py-1 rounded-md">
                  {exp.company}
                </span>
              </div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                {exp.start_date} — {exp.current ? 'PRESENT' : exp.end_date}
              </p>
              <p className="text-sm text-gray-500 font-medium leading-relaxed max-w-2xl">
                {exp.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
