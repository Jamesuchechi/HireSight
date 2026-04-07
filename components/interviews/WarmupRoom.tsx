"use client";

import { useState, useEffect, useRef } from "react";
import { 
    Video, Mic, MicOff, VideoOff, 
    ShieldCheck, Zap, ArrowRight,
    Volume2, Settings, AlertCircle,
    CheckCircle2, Loader2
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface WarmupRoomProps {
    onReady: () => void;
    candidateName: string;
    interviewType: string;
}

export default function WarmupRoom({ onReady, candidateName, interviewType }: WarmupRoomProps) {
    const [videoEnabled, setVideoEnabled] = useState(true);
    const [audioEnabled, setAudioEnabled] = useState(true);
    const [stream, setStream] = useState<MediaStream | null>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    const [checking, setChecking] = useState(true);

    useEffect(() => {
        async function setupMedia() {
            try {
                const s = await navigator.mediaDevices.getUserMedia({ 
                    video: true, 
                    audio: true 
                });
                setStream(s);
                if (videoRef.current) videoRef.current.srcObject = s;
                setChecking(false);
            } catch (err) {
                console.error("Media Access Denied:", err);
                setChecking(false);
            }
        }
        setupMedia();

        return () => {
            stream?.getTracks().forEach(track => track.stop());
        };
    }, []);

    const toggleVideo = () => {
        if (stream) {
            const videoTrack = stream.getVideoTracks()[0];
            videoTrack.enabled = !videoEnabled;
            setVideoEnabled(!videoEnabled);
        }
    };

    const toggleAudio = () => {
        if (stream) {
            const audioTrack = stream.getAudioTracks()[0];
            audioTrack.enabled = !audioEnabled;
            setAudioEnabled(!audioEnabled);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] bg-[#0c0c0c] flex items-center justify-center p-8 overflow-hidden">
            {/* Background Atmosphere */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 blur-[120px] rounded-full translate-x-1/3 -translate-y-1/3" />
                <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-amber-500/5 blur-[120px] rounded-full -translate-x-1/3 translate-y-1/3" />
            </div>

            <div className="relative w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                {/* Left: Video Preview */}
                <div className="space-y-8">
                    <div className="relative aspect-video bg-zinc-900 rounded-[48px] overflow-hidden border border-white/10 shadow-2xl group">
                        {!videoEnabled || !stream ? (
                            <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                                <div className="p-6 bg-white/5 rounded-full">
                                     <VideoOff className="w-12 h-12 text-gray-500" />
                                </div>
                                <p className="text-[10px] font-black text-gray-500 uppercase italic tracking-[0.3em]">Visual Feed Offline</p>
                            </div>
                        ) : (
                            <video 
                                ref={videoRef} 
                                autoPlay 
                                muted 
                                playsInline 
                                className="w-full h-full object-cover mirror"
                            />
                        )}

                        {/* Video Overlay Controls */}
                        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center space-x-4">
                            <button 
                                onClick={toggleAudio}
                                className={`p-5 rounded-3xl backdrop-blur-xl border transition-all ${
                                    audioEnabled ? 'bg-white/10 border-white/10 text-white' : 'bg-red-500/20 border-red-500/20 text-red-500'
                                }`}
                            >
                                {audioEnabled ? <Mic className="w-6 h-6" /> : <MicOff className="w-6 h-6" />}
                            </button>
                            <button 
                                onClick={toggleVideo}
                                className={`p-5 rounded-3xl backdrop-blur-xl border transition-all ${
                                    videoEnabled ? 'bg-white/10 border-white/10 text-white' : 'bg-red-500/20 border-red-500/20 text-red-500'
                                }`}
                            >
                                {videoEnabled ? <Video className="w-6 h-6" /> : <VideoOff className="w-6 h-6" />}
                            </button>
                        </div>

                        {/* Neural Mapping Animation */}
                        {videoEnabled && stream && (
                            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-primary/40 to-transparent animate-scan" />
                        )}
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                        <StatusIndicator label="Camera" active={!!stream?.getVideoTracks()[0]} />
                        <StatusIndicator label="Microphone" active={!!stream?.getAudioTracks()[0]} />
                        <StatusIndicator label="Neural Sync" active={!checking} />
                    </div>
                </div>

                {/* Right: Briefing */}
                <div className="space-y-12">
                    <header className="space-y-4">
                         <div className="flex items-center space-x-3">
                             <div className="p-2 bg-primary/10 rounded-lg">
                                 <ShieldCheck className="w-4 h-4 text-primary" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic">Pre-Flight Authorization</span>
                         </div>
                         <h1 className="text-6xl font-black text-white italic tracking-tighter leading-none uppercase">
                            Engage <span className="text-primary italic">Protocol</span>
                         </h1>
                         <p className="text-xl font-bold text-gray-400 italic leading-relaxed">
                            Awaiting tactical entry for <span className="text-white italic">{interviewType} Mission</span> with <span className="text-white italic">{candidateName}</span>.
                         </p>
                    </header>

                    <div className="space-y-6">
                        <BriefingItem 
                            icon={<Zap className="w-4 h-4" />}
                            title="Tactical Readiness"
                            desc="Ensure your environment is free of distractions and lighting is optimized for facial recognition scan."
                        />
                        <BriefingItem 
                            icon={<Volume2 className="w-4 h-4" />}
                            title="Comm-Check"
                            desc="Speak clearly into your designated input device. Real-time transcription will be active during the session."
                        />
                    </div>

                    <button 
                        onClick={onReady}
                        className="w-full py-8 bg-primary text-white rounded-[32px] font-black text-xs uppercase tracking-[0.4em] italic hover:scale-[1.02] active:scale-[0.98] transition-all shadow-2xl shadow-primary/20 flex items-center justify-center space-x-4 group"
                    >
                        <span>Initiate Deployment</span>
                        <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                    </button>

                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest text-center italic">
                        By deploying, you agree to the Neural Recording Protocol.
                    </p>
                </div>
            </div>
        </div>
    );
}

function StatusIndicator({ label, active }: { label: string, active: boolean }) {
    return (
        <div className="px-6 py-4 bg-white/5 rounded-3xl border border-white/5 flex items-center justify-between">
            <span className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic">{label}</span>
            {active ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            ) : (
                <Loader2 className="w-4 h-4 text-primary animate-spin" />
            )}
        </div>
    );
}

function BriefingItem({ icon, title, desc }: any) {
    return (
        <div className="flex items-start space-x-4 group">
            <div className="p-3 bg-white/5 text-gray-400 rounded-2xl group-hover:text-primary transition-colors border border-white/5">
                {icon}
            </div>
            <div>
                <h4 className="text-sm font-black text-white italic uppercase tracking-widest mb-1">{title}</h4>
                <p className="text-xs font-bold text-gray-500 italic leading-relaxed">{desc}</p>
            </div>
        </div>
    );
}
