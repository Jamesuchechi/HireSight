"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { BrainCircuit, Mic, MicOff, Volume2, VolumeX, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ClientSideAvaProps {
  roomName: string;
}

export default function ClientSideAva({ roomName }: ClientSideAvaProps) {
  const [isListening, setIsListening] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const messagesRef = useRef<any[]>([]);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        let currentTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);

        // Reset silence timer on speech
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = setTimeout(() => {
          if (currentTranscript.trim()) {
            handleSpeechEnd(currentTranscript);
          }
        }, 2000); // 2 seconds of silence triggers response
      };

      recognition.onerror = (event: any) => {
        console.error("Speech recognition error", event.error);
        if (event.error === 'not-allowed') {
          setError("Microphone access denied.");
        }
      };

      recognitionRef.current = recognition;
    } else {
      setError("Speech recognition not supported in this browser.");
    }

    return () => {
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  const handleSpeechEnd = async (text: string) => {
    if (!text.trim() || isThinking || isSpeaking) return;

    recognitionRef.current?.stop();
    setIsListening(false);
    setIsThinking(true);
    setTranscript("");

    const userMessage = { role: "user", content: text };
    messagesRef.current.push(userMessage);

    try {
      const res = await fetch("/api/ava", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: messagesRef.current }),
      });

      const data = await res.json();
      if (data.error) throw new Error(data.error);

      const aiText = data.text;
      setResponse(aiText);
      messagesRef.current.push({ role: "assistant", content: aiText });
      
      speak(aiText);
    } catch (err: any) {
      setError("Ava failed to think. Connection interrupted.");
      console.error(err);
    } finally {
      setIsThinking(false);
    }
  };

  const speak = (text: string) => {
    if (!window.speechSynthesis) return;

    // Cancel any ongoing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Attempt to find a premium-sounding voice (browser dependent)
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.name.includes("Google") || v.name.includes("Samantha") || v.name.includes("Daniel")) || voices[0];
    if (preferredVoice) utterance.voice = preferredVoice;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      // Restart listening after speaking
      if (recognitionRef.current) {
        recognitionRef.current.start();
        setIsListening(true);
      }
    };

    window.speechSynthesis.speak(utterance);
  };

  const toggleAva = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      setError(null);
      try {
        recognitionRef.current?.start();
        setIsListening(true);
        // Intro message if first time
        if (messagesRef.current.length === 0) {
            const intro = "Screening Protocol Initiated. I am Ava. It is a pleasure to meet you. Let's begin the tactical assessment. Please introduce yourself.";
            setResponse(intro);
            messagesRef.current.push({ role: "assistant", content: intro });
            speak(intro);
        }
      } catch (e) {
        console.error("Start failed", e);
      }
    }
  };

  return (
    <div className="absolute inset-x-6 bottom-32 flex flex-col items-center pointer-events-none space-y-4">
      <AnimatePresence>
        {isThinking && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="bg-primary/20 backdrop-blur-xl border border-primary/30 px-6 py-2 rounded-full flex items-center space-x-3"
          >
            <Loader2 className="w-3 h-3 text-primary animate-spin" />
            <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic">Ava is thinking...</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center space-x-4 pointer-events-auto">
        {/* Status indicator / Control */}
        <button 
          onClick={toggleAva}
          className={`p-5 rounded-[32px] border transition-all duration-500 group relative ${
            isListening 
              ? 'bg-primary border-primary text-white shadow-[0_0_30px_rgba(var(--primary-rgb),0.5)]' 
              : 'bg-zinc-900/80 border-white/10 text-gray-400 hover:text-white'
          }`}
        >
          {isSpeaking ? (
            <div className="flex items-center space-x-1">
              {[1, 2, 3].map(i => (
                <motion.div 
                  key={i}
                  animate={{ height: [8, 20, 8] }}
                  transition={{ repeat: Infinity, duration: 0.5, delay: i * 0.1 }}
                  className="w-1 bg-white rounded-full"
                />
              ))}
            </div>
          ) : isListening ? (
            <Mic className="w-6 h-6 animate-pulse" />
          ) : (
             <MicOff className="w-6 h-6" />
          )}

          {/* Label Tooltip */}
          <div className="absolute -top-12 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap bg-black/80 px-4 py-2 rounded-xl text-[8px] font-black uppercase tracking-widest italic border border-white/5">
             {isListening ? 'Ava is Listening' : 'Activate Ava Protocol'}
          </div>
        </button>

        {/* Info Box */}
        {(transcript || response) && (
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="max-w-md bg-black/60 backdrop-blur-3xl border border-white/5 rounded-[32px] p-6 space-y-2 shadow-2xl"
          >
            <div className="flex items-center space-x-2 text-primary">
               <BrainCircuit className="w-4 h-4" />
               <span className="text-[8px] font-black uppercase tracking-widest italic">Mission Objective Hub</span>
            </div>
            
            {transcript && (
              <p className="text-xs font-bold text-gray-400 italic">"{transcript}"</p>
            )}
            
            {response && (
              <p className="text-xs font-black text-white leading-relaxed">{response}</p>
            )}
          </motion.div>
        )}
      </div>

      {error && (
        <p className="text-[8px] font-black text-red-500 uppercase tracking-widest italic animate-pulse">{error}</p>
      )}
    </div>
  );
}
