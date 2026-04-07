import { Briefcase, Zap, Star, Users } from "lucide-react";

interface ProfileStatsProps {
  stats: {
    label: string;
    value: string | number;
    icon: any;
    color: string;
    bgColor: string;
    borderColor: string;
  }[];
}

export default function ProfileStats({ stats }: ProfileStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
      {stats.map((stat, i) => (
        <div 
          key={i} 
          className={`p-4 ${stat.bgColor} rounded-[28px] border ${stat.borderColor} text-center group hover:scale-[1.02] transition-all`}
        >
          <div className="flex justify-center mb-2">
            <stat.icon className={`w-5 h-5 ${stat.color} opacity-70`} />
          </div>
          <div className={`text-2xl font-black ${stat.color} italic`}>{stat.value}</div>
          <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest mt-1">{stat.label}</div>
        </div>
      ))}
    </div>
  );
}
