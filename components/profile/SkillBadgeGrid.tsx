import { Skill } from "@/types/profile";

interface SkillBadgeGridProps {
  skills: Skill[];
}

export default function SkillBadgeGrid({ skills }: SkillBadgeGridProps) {
  if (!skills || skills.length === 0) {
    return (
      <div className="text-center py-6 bg-gray-50 rounded-[32px] border border-dashed border-gray-200">
        <p className="text-sm font-bold text-gray-400 uppercase tracking-widest">No skill signatures detected</p>
      </div>
    );
  }

  const getProficiencyColor = (level: string) => {
    switch (level) {
      case 'expert': return 'bg-zinc-900 border-primary text-primary';
      case 'advanced': return 'bg-white border-zinc-900 text-zinc-900';
      case 'intermediate': return 'bg-gray-50 border-gray-200 text-gray-600';
      default: return 'bg-gray-50 border-gray-100 text-gray-400';
    }
  };

  return (
    <div className="flex flex-wrap gap-3">
      {skills.map((skill, i) => (
        <div 
          key={i} 
          className={`px-5 py-2.5 rounded-2xl border-2 font-black italic text-xs uppercase tracking-widest transition-all hover:scale-105 ${getProficiencyColor(skill.proficiency)}`}
        >
          {skill.skill}
        </div>
      ))}
    </div>
  );
}
