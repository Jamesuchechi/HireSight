"use client";

import {
  ControlBar,
  GridLayout,
  LiveKitRoom,
  ParticipantTile,
  RoomAudioRenderer,
  useTracks,
  useRoomContext,
} from "@livekit/components-react";
import "@livekit/components-styles";
import { Track } from "livekit-client";
import { useEffect, useState } from "react";
import { Loader2, VideoOff, MicOff, Settings } from "lucide-react";
import ClientSideAva from "./ClientSideAva";

interface VideoRoomProps {
  token: string;
  roomName: string;
  onDisconnected?: () => void;
  onMessage?: (payload: any) => void;
}

export default function VideoRoom({ token, roomName, onDisconnected, onMessage }: VideoRoomProps) {
  if (!token) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-zinc-900 rounded-[32px] border border-white/5 space-y-4">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest italic">Establishing Link...</p>
      </div>
    );
  }

  return (
    <LiveKitRoom
      video={true}
      audio={true}
      token={token}
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      onDisconnected={onDisconnected}
      connect={true}
      className="relative h-full w-full bg-zinc-950 rounded-[40px] overflow-hidden border border-white/10 shadow-2xl"
    >
      <VideoConferenceContent roomName={roomName} onMessage={onMessage} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function VideoConferenceContent({ roomName, onMessage }: { roomName: string, onMessage?: (payload: any) => void }) {
  const room = useRoomContext();
  const [messages, setMessages] = useState<any[]>([]);
  
  useEffect(() => {
    if (!room) return;
    const handleData = (payload: Uint8Array, participant?: any) => {
      const decoder = new TextDecoder();
      const str = decoder.decode(payload);
      try {
        const data = JSON.parse(str);
        if (data.type === 'whisper') {
          onMessage?.({ ...data, from: participant?.identity });
        }
      } catch (e) {
        console.error("Failed to parse mission data:", e);
      }
    };

    room.on('dataReceived', handleData);
    return () => {
      room.off('dataReceived', handleData);
    };
  }, [room, onMessage]);

  const tracks = useTracks(
    [
      { source: Track.Source.Camera, withPlaceholder: true },
      { source: Track.Source.ScreenShare, withPlaceholder: false },
    ],
    { onlySubscribed: false }
  );

  return (
    <div className="flex flex-col h-full relative group">
      {/* Participant Grid */}
      <div className="flex-1 p-4">
          <GridLayout tracks={tracks} className="h-full gap-4">
            <ParticipantTile />
          </GridLayout>
      </div>

      {/* Modern Floating Control Bar */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-all duration-500 scale-95 group-hover:scale-100">
          <div className="bg-zinc-900/80 backdrop-blur-xl border border-white/10 p-2 rounded-full shadow-2xl flex items-center space-x-2">
              <ControlBar 
                variation="minimal" 
                controls={{ leave: false, settings: true }}
              />
              <div className="h-8 w-px bg-white/10 mx-2" />
              <button 
                className="p-3 bg-red-500/20 text-red-500 rounded-full hover:bg-red-500 hover:text-white transition-all font-black text-[10px] uppercase tracking-widest italic px-6"
                onClick={() => window.location.href = '/dashboard/interviews'}
              >
                  Abort Mission
              </button>
          </div>
      </div>

      {/* Room Overlay Info */}
      <div className="absolute top-6 left-6 p-4 bg-black/40 backdrop-blur-md rounded-2xl border border-white/10 pointer-events-none">
          <div className="flex items-center space-x-3">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[10px] font-black text-white uppercase tracking-widest italic leading-none">Live Protocol Encrypted</span>
          </div>
      </div>

      {/* Client-Side Ava Assistant */}
      <ClientSideAva roomName={roomName} />
    </div>
  );
}
