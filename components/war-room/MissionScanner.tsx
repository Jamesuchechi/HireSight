"use client";

import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, ResponsiveContainer } from "recharts";

interface MissionScannerProps {
    data: any[];
}

export default function MissionScanner({ data }: MissionScannerProps) {
    // Transform data for the radar chart (Example: Avg scores across categories)
    // Default mock if no data provided
    const chartData = data?.length > 0 ? data : [
        { subject: 'Technical', A: 120, fullMark: 150 },
        { subject: 'Architecture', A: 98, fullMark: 150 },
        { subject: 'Behavioral', A: 86, fullMark: 150 },
        { subject: 'Communication', A: 99, fullMark: 150 },
        { subject: 'STAR Compliance', A: 85, fullMark: 150 },
        { subject: 'Engagement', A: 65, fullMark: 150 },
    ];

    return (
        <div className="relative aspect-square w-full">
            {/* Radar Background Effects */}
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-[80%] h-[80%] border border-primary/20 rounded-full animate-ping opacity-20" />
                <div className="w-[60%] h-[60%] border border-primary/20 rounded-full animate-pulse opacity-10" />
            </div>

            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={chartData}>
                    <PolarGrid stroke="#27272a" />
                    <PolarAngleAxis 
                        dataKey="subject" 
                        tick={{ fill: '#71717a', fontSize: 8, fontWeight: '900', letterSpacing: '0.1em' }} 
                    />
                    <Radar
                        name="Protocol Health"
                        dataKey="A"
                        stroke="#f43f5e"
                        fill="#f43f5e"
                        fillOpacity={0.3}
                        animationBegin={0}
                        animationDuration={1500}
                    />
                </RadarChart>
            </ResponsiveContainer>

            {/* Scanning Line Overlay */}
            <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 flex items-center justify-center pointer-events-none"
            >
                <div className="w-[50%] h-[1px] bg-gradient-to-r from-primary to-transparent origin-left -translate-x-full" />
            </motion.div>

            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-zinc-900 border border-white/10 rounded-full">
                <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest italic leading-none flex items-center space-x-2">
                    <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
                    <span>Real-time Mission Scanning Active</span>
                </p>
            </div>
        </div>
    );
}
