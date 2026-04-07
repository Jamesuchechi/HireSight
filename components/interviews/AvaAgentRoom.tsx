"use client";

import { useEffect, useState, useRef } from "react";
import { 
    LiveKitRoom, 
    RoomAudioRenderer, 
    ControlBar, 
    useVoiceAssistant, 
    BarVisualizer,
    VoiceAssistantControlBar,
    AgentBarVisualizer,
    ConnectionState
} from "@livekit/components-react";
import { 
    Mic, MicOff, ShieldCheck, Zap, 
    BrainCircuit, MessageSquare, 
    Loader2, ArrowLeft, Headphones
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";

interface AvaAgentRoomProps {
    roomId: string;
    token: string;
    url: string;
    onComplete: (summary: any) => void;
}

export default function AvaAgentRoom({ roomId, token, url, onComplete }: AvaAgentRoomProps) {
    const router = useRouter();

    return (
        <div className="fixed inset-0 z-[100] bg-[#0c0c0c] flex flex-col overflow-hidden">
            {/* Atmosphere */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 blur-[120px] rounded-full translate-x-1/3 -translate-y-1/3" />
                <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-500/5 blur-[120px] rounded-full -translate-x-1/3 translate-y-1/3" />
            </div>

            <LiveKitRoom
                token={token}
                serverUrl={url}
                connect={true}
                audio={true}
                video={false}
                className="flex-grow flex flex-col relative z-10"
            >
                <AvaInterface onComplete={onComplete} />
                <RoomAudioRenderer />
            </LiveKitRoom>
        </div>
    );
}

function AvaInterface({ onComplete }: { onComplete: (summary: any) => void }) {
    const router = useRouter();
    const { state, audioTrack, agentTranscripts } = useVoiceAssistant();

    return (
        <div className="flex-grow flex flex-col items-center justify-center p-12 space-y-16">
            {/* Mission Header */}
            <header className="fixed top-12 inset-x-12 flex items-center justify-between">
                <div className="flex items-center space-x-6">
                    <button 
                        onClick={() => router.back()}
                        className="p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-all text-gray-400 group"
                    >
                        <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                    </button>
                    <div className="space-y-1">
                        <div className="flex items-center space-x-3">
                             <div className="p-1.5 bg-primary/10 rounded-lg">
                                 <BrainCircuit className="w-4 h-4 text-primary" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic leading-none">Ava Protocol Active</span>
                        </div>
                        <h2 className="text-2xl font-black text-white italic tracking-tighter uppercase leading-none">Autonomous <span className="text-primary italic">Screening</span></h2>
                    </div>
                </div>

                <div className="flex items-center space-x-4 px-6 py-3 bg-white/5 rounded-2xl border border-white/5">
                    <Headphones className="w-4 h-4 text-gray-500" />
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic line-clamp-1">Audio-Only Engagement Matrix</span>
                </div>
            </header>

            {/* Neural Visualizer Central */}
            <div className="relative w-full max-w-2xl aspect-square flex items-center justify-center">
                
                {/* Background Concentric Rings */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <motion.div 
                        animate={{ scale: [1, 1.1, 1], opacity: [0.1, 0.2, 0.1] }}
                        transition={{ duration: 4, repeat: Infinity }}
                        className="w-[80%] h-[80%] border border-primary/20 rounded-full" 
                    />
                    <motion.div 
                        animate={{ scale: [1, 1.2, 1], opacity: [0.05, 0.1, 0.05] }}
                        transition={{ duration: 6, repeat: Infinity }}
                        className="w-full h-full border border-white/5 rounded-full" 
                    />
                </div>

                {/* Primary Voice Waveform */}
                <div className="relative z-20 w-80 h-80 bg-zinc-900 rounded-full flex items-center justify-center border border-white/10 shadow-2xl overflow-hidden">
                    <AnimatePresence mode="wait">
                         {state === 'thinking' ? (
                             <motion.div 
                                key="thinking"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 1.2 }}
                                className="flex flex-col items-center space-y-4"
                             >
                                 <Loader2 className="w-12 h-12 text-primary animate-spin" />
                                 <p className="text-[10px] font-black text-primary uppercase tracking-[0.3em] italic animate-pulse">Calculating Intelligence</p>
                             </motion.div>
                         ) : (
                             <motion.div 
                                key="visualizer"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="w-full h-full flex items-center justify-center p-8"
                             >
                                 <BarVisualizer 
                                    className="w-full h-40 text-primary" 
                                    barCount={32}
                                    gap={4}
                                 />
                             </motion.div>
                         )}
                    </AnimatePresence>

                    {/* Aura Glow */}
                    <div className={`absolute inset-0 transition-opacity duration-1000 ${state === 'speaking' ? 'bg-primary/5 opacity-100' : 'opacity-0'}`} />
                </div>

                {/* Tactical HUD Overlays */}
                <HUDElement 
                    position="top-8 left-8" 
                    icon={<Zap className="w-4 h-4 text-amber-500" />} 
                    label="Latency Score" 
                    value="122ms" 
                />
                <HUDElement 
                    position="bottom-8 right-8" 
                    icon={<MessageSquare className="w-4 h-4 text-indigo-400" />} 
                    label="Context Depth" 
                    value="High" 
                />
            </div>

            {/* Transcript Live Feed (Subtle) */}
            <div className="w-full max-w-xl h-24 overflow-hidden relative">
                 <AnimatePresence mode="popLayout">
                    {agentTranscripts.slice(-1).map((transcript) => (
                        <motion.p
                            key={transcript.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="text-lg font-bold text-gray-400 text-center italic leading-relaxed"
                        >
                            "{transcript.text}"
                        </motion.p>
                    ))}
                 </AnimatePresence>
                 <div className="absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-[#0c0c0c] to-transparent pointer-events-none" />
                 <div className="absolute inset-x-0 bottom-0 h-8 bg-gradient-to-t from-[#0c0c0c] to-transparent pointer-events-none" />
            </div>

            {/* Controls Bar */}
            <div className="fixed bottom-12 inset-x-0 flex flex-col items-center space-y-8">
                 <div className="p-6 bg-zinc-900 border border-white/10 rounded-[32px] shadow-2xl flex items-center space-x-8">
                    <VoiceAssistantControlBar />
                 </div>

                 <p className="text-[10px] font-black text-gray-600 uppercase tracking-widest italic animate-pulse">
                     Encryption Protocol Multi-Node Auth Enabled
                 </p>
            </div>
        </div>
    );
}

function HUDElement({ position, icon, label, value }: any) {
    return (
        <div className={`absolute ${position} flex flex-col space-y-2`}>
            <div className="flex items-center space-x-3">
                <div className="p-2 bg-white/5 rounded-xl border border-white/10">
                    {icon}
                </div>
                <div>
                    <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest mb-1">{label}</p>
                    <p className="text-xs font-black text-white italic uppercase">{value}</p>
                </div>
            </div>
        </div>
    );
}
