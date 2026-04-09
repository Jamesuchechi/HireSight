"use client";

import { useEffect, useState, useRef } from "react";
import { 
    LiveKitRoom, 
    RoomAudioRenderer, 
    ControlBar, 
    useVoiceAssistant, 
    BarVisualizer,
    VoiceAssistantControlBar,
    ConnectionState
} from "@livekit/components-react";
import { Room, RoomEvent } from "livekit-client";
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
        <div className="relative w-full h-full min-h-[500px] bg-[#0c0c0c] flex flex-col overflow-hidden rounded-[32px] border border-white/5 neural-grid">
            {/* Atmosphere */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/10 blur-[100px] rounded-full translate-x-1/3 -translate-y-1/3" />
                <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-indigo-500/10 blur-[100px] rounded-full -translate-x-1/3 translate-y-1/3" />
            </div>

            <LiveKitRoom
                serverUrl={url}
                token={token}
                connect={true}
                audio={true}
                video={false}
                options={{
                    publishDefaults: {
                    },
                }}
                className="flex-grow flex flex-col relative z-10 p-12"
            >
                <AvaInterface onComplete={onComplete} />
                <RoomAudioRenderer />
            </LiveKitRoom>
        </div>
    );
}


function AvaInterface({ onComplete }: { onComplete: (summary: any) => void }) {
    const router = useRouter();
    const { state, audioTrack } = useVoiceAssistant();
    // Temporary bypass for transcript types in this version
    const agentTranscripts: any[] = [];

    return (
        <div className="flex-grow flex flex-col items-center justify-between pb-8">

            {/* Neural Visualizer Central */}
            <div className="relative w-full max-w-lg aspect-square flex items-center justify-center">
                
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
                <div className="relative z-20 w-64 h-64 bg-zinc-900 rounded-full flex items-center justify-center border border-white/10 shadow-2xl overflow-hidden">
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
                                 />
                             </motion.div>
                         )}
                    </AnimatePresence>

                    {/* Aura Glow */}
                    <div className={`absolute inset-0 transition-opacity duration-1000 ${state === 'speaking' ? 'bg-primary/5 opacity-100' : 'opacity-0'}`} />
                </div>

                {/* Tactical HUD Overlays - Adjusted for smaller container */}
                <HUDElement 
                    position="top-0 left-0" 
                    icon={<Zap className="w-4 h-4 text-amber-500" />} 
                    label="Latency Score" 
                    value="122ms" 
                />
                <HUDElement 
                    position="bottom-0 right-0" 
                    icon={<MessageSquare className="w-4 h-4 text-indigo-400" />} 
                    label="Context Depth" 
                    value="High" 
                />
            </div>

            {/* Transcript Live Feed (Subtle) */}
            <div className="w-full max-w-xl h-32 overflow-hidden relative">
                 <AnimatePresence mode="popLayout">
                    {agentTranscripts?.slice(-1).map((transcript) => (
                        <motion.p
                            key={transcript.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="text-xl font-black text-white text-center italic leading-relaxed drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]"
                        >
                            "{transcript.text}"
                        </motion.p>
                    ))}
                 </AnimatePresence>
                 <div className="absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-[#0c0c0c] to-transparent pointer-events-none" />
                 <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-[#0c0c0c] to-transparent pointer-events-none" />
            </div>

            {/* Controls Bar */}
            <div className="w-full flex flex-col items-center space-y-4">
                 <div className="p-4 bg-zinc-900 border border-white/5 rounded-3xl shadow-2xl flex items-center space-x-8">
                    <VoiceAssistantControlBar />
                 </div>
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
