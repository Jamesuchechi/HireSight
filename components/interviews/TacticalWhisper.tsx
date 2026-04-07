"use client";

import { useState } from "react";
import { MessageSquare, Send, ShieldAlert, Cpu } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRoomContext } from "@livekit/components-react";

interface Whisper {
    id: string;
    from: string;
    text: string;
    timestamp: Date;
}

export function TacticalWhisperInput({ role }: { role: string }) {
    const { room } = useRoomContext();
    const [text, setText] = useState("");

    const sendWhisper = async () => {
        if (!text.trim() || !room) return;
        
        const payload = JSON.stringify({
            type: 'whisper',
            text: text.trim(),
            timestamp: new Date().toISOString()
        });

        const encoder = new TextEncoder();
        await room.localParticipant.publishData(encoder.encode(payload), { reliable: true });
        setText("");
    };

    if (role !== 'observer' && role !== 'interviewer') return null;

    return (
        <div className="bg-zinc-900 border border-white/5 rounded-[32px] p-6 space-y-4">
             <div className="flex items-center space-x-3 mb-2">
                 <div className="p-2 bg-primary/10 rounded-xl">
                     <ShieldAlert className="w-4 h-4 text-primary" />
                 </div>
                 <h5 className="text-[10px] font-black text-white uppercase tracking-[0.2em] italic">Tactical Whisper Channel</h5>
             </div>
             
             <div className="relative">
                 <input 
                    type="text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendWhisper()}
                    placeholder="Dispatch private intel to interviewer..."
                    className="w-full bg-black/40 border border-white/10 rounded-2xl py-3 pl-5 pr-12 text-xs font-bold text-white placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary/20"
                 />
                 <button 
                    onClick={sendWhisper}
                    className="absolute right-2 top-1.5 p-2 bg-primary text-white rounded-xl hover:scale-105 transition-all shadow-lg"
                 >
                    <Send className="w-4 h-4" />
                 </button>
             </div>
             <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest italic text-center">
                 Direct encrypted link to primary interviewer. Candidate blind.
             </p>
        </div>
    );
}

export function WhisperFeed({ whispers }: { whispers: Whisper[] }) {
    return (
        <div className="fixed bottom-32 right-12 w-80 z-[60] flex flex-col space-y-3 pointer-events-none">
            <AnimatePresence mode="popLayout">
                {whispers.map((w) => (
                    <motion.div
                        key={w.id}
                        initial={{ opacity: 0, x: 50, scale: 0.9 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="bg-zinc-900/90 backdrop-blur-3xl border border-primary/30 p-5 rounded-3xl shadow-2xl pointer-events-auto"
                    >
                        <div className="flex items-center space-x-3 mb-2">
                            <div className="p-1.5 bg-primary/20 rounded-lg">
                                <Cpu className="w-3 h-3 text-primary animate-pulse" />
                            </div>
                            <span className="text-[9px] font-black text-primary uppercase tracking-widest italic">{w.from} (Whisper)</span>
                        </div>
                        <p className="text-xs font-bold text-white leading-relaxed italic">
                            "{w.text}"
                        </p>
                    </motion.div>
                ))}
            </AnimatePresence>
        </div>
    );
}
