"use client";

import { useEffect, useState, useRef } from "react";
import { 
    Play, Pause, SkipBack, SkipForward, 
    Volume2, VolumeX, Maximize, BrainCircuit,
    Star, AlertCircle, Clock, Zap
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface TacticalEvent {
    timestamp: number; // in seconds
    type: 'star_s' | 'star_t' | 'star_a' | 'star_r' | 'red_flag' | 'insight';
    message: string;
}

interface TacticalReplayProps {
    videoUrl: string;
    events: TacticalEvent[];
    title: string;
}

export default function TacticalReplay({ videoUrl, events, title }: TacticalReplayProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [showControls, setShowControls] = useState(true);
    const [loading, setLoading] = useState(true);

    const togglePlay = () => {
        if (videoRef.current) {
            if (isPlaying) videoRef.current.pause();
            else videoRef.current.play();
            setIsPlaying(!isPlaying);
        }
    };

    const handleTimeUpdate = () => {
        if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
    };

    const handleLoadedMetadata = () => {
        if (videoRef.current) setDuration(videoRef.current.duration);
        setLoading(false);
    };

    const seek = (time: number) => {
        if (videoRef.current) {
            videoRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // Auto-hide controls
    useEffect(() => {
        let timer: any;
        if (isPlaying && showControls) {
            timer = setTimeout(() => setShowControls(false), 3000);
        }
        return () => clearTimeout(timer);
    }, [isPlaying, showControls]);

    return (
        <div 
            className="relative bg-black rounded-[40px] overflow-hidden group shadow-2xl border border-white/5 aspect-video"
            onMouseMove={() => setShowControls(true)}
        >
            <video
                ref={videoRef}
                src={videoUrl}
                className="w-full h-full object-contain"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onClick={togglePlay}
            />

            {/* Overlay: Header */}
            <div className={`absolute top-0 inset-x-0 p-8 bg-gradient-to-b from-black/80 to-transparent transition-opacity duration-500 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
                <div className="flex items-center justify-between">
                    <div className="space-y-1">
                         <div className="flex items-center space-x-3">
                             <div className="p-1.5 bg-primary/20 rounded-lg">
                                 <BrainCircuit className="w-4 h-4 text-primary" />
                             </div>
                             <span className="text-[10px] font-black text-primary uppercase tracking-[0.4em] italic">Tactical Replay Engaged</span>
                         </div>
                         <h3 className="text-xl font-black text-white italic tracking-tighter uppercase">{title}</h3>
                    </div>
                    <div className="px-4 py-2 bg-white/10 rounded-xl backdrop-blur-md border border-white/10">
                        <span className="text-[10px] font-black text-gray-300 uppercase tracking-widest italic">Source: Mission Recording</span>
                    </div>
                </div>
            </div>

            {/* AI Critical Moments (Visual Markers) */}
            <div className={`absolute bottom-24 inset-x-8 h-1 flex items-center transition-opacity duration-500 ${showControls ? 'opacity-100' : 'opacity-0'}`}>
                {events.map((event, idx) => {
                    const position = (event.timestamp / duration) * 100;
                    if (isNaN(position)) return null;
                    return (
                        <motion.div
                            key={idx}
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            whileHover={{ scale: 1.5 }}
                            className="absolute z-30 cursor-pointer"
                            style={{ left: `${position}%` }}
                            onClick={(e) => { e.stopPropagation(); seek(event.timestamp); }}
                        >
                            <div className={`w-3 h-3 rounded-full border-2 border-black flex items-center justify-center ${
                                event.type.startsWith('star') ? 'bg-primary shadow-[0_0_10px_#f43f5e]' :
                                event.type === 'red_flag' ? 'bg-amber-500 shadow-[0_0_10px_#f59e0b]' : 'bg-indigo-500'
                            }`}>
                                <div className="hidden group-hover:block absolute bottom-6 px-3 py-1.5 bg-zinc-900 text-white rounded-lg text-[8px] font-black uppercase tracking-widest whitespace-nowrap shadow-2xl">
                                    {event.message} ({formatTime(event.timestamp)})
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Custom Controls Bar */}
            <AnimatePresence>
                {showControls && (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="absolute bottom-0 inset-x-0 p-8 bg-gradient-to-t from-black/80 via-black/40 to-transparent flex flex-col space-y-6"
                    >
                        {/* Progress Bar */}
                        <div className="relative group/progress h-1 hover:h-2 transition-all cursor-pointer bg-white/20 rounded-full"
                             onClick={(e) => {
                                 const rect = e.currentTarget.getBoundingClientRect();
                                 const x = e.clientX - rect.left;
                                 seek((x / rect.width) * duration);
                             }}
                        >
                            <div 
                                className="absolute h-full bg-primary rounded-full" 
                                style={{ width: `${(currentTime / duration) * 100}%` }} 
                            />
                            <div 
                                className="absolute w-3 h-3 bg-white rounded-full -translate-y-1 opacity-0 group-hover/progress:opacity-100 transition-opacity"
                                style={{ left: `calc(${(currentTime / duration) * 100}% - 6px)` }}
                            />
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-8">
                                <button onClick={togglePlay} className="text-white hover:text-primary transition-colors">
                                    {isPlaying ? <Pause className="w-8 h-8 fill-current" /> : <Play className="w-8 h-8 fill-current" />}
                                </button>
                                
                                <div className="flex items-center space-x-4">
                                     <button onClick={() => seek(currentTime - 10)} className="text-gray-400 hover:text-white transition-colors">
                                         <SkipBack className="w-5 h-5" />
                                     </button>
                                     <button onClick={() => seek(currentTime + 10)} className="text-gray-400 hover:text-white transition-colors">
                                         <SkipForward className="w-5 h-5" />
                                     </button>
                                </div>

                                <div className="text-[10px] font-black text-gray-300 tabular-nums tracking-widest italic">
                                    {formatTime(currentTime)} / {formatTime(duration)}
                                </div>
                            </div>

                            <div className="flex items-center space-x-6">
                                <div className="flex items-center space-x-4">
                                    <button onClick={() => setIsMuted(!isMuted)} className="text-gray-400 hover:text-white transition-all">
                                        {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                                    </button>
                                    <input 
                                        type="range" min="0" max="1" step="0.1" 
                                        value={volume} 
                                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                                        className="w-20 accent-primary" 
                                    />
                                </div>
                                <button className="text-gray-400 hover:text-white transition-all">
                                    <Maximize className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Play/Pause Large Overlay */}
            <div 
                className={`absolute inset-0 flex items-center justify-center pointer-events-none transition-opacity duration-300 ${!isPlaying && !loading ? 'opacity-100' : 'opacity-0'}`}
                onClick={togglePlay}
            >
                <div className="w-24 h-24 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center border border-white/10 shadow-2xl">
                    <Play className="w-10 h-10 text-white fill-current ml-2" />
                </div>
            </div>
        </div>
    );
}
