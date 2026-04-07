"use client";

import { useEffect, useRef, useState } from "react";
import Editor, { OnMount } from "@monaco-editor/react";
import * as Y from "yjs";
import { MonacoBinding } from "y-monaco";
import { createClient } from "@/lib/supabase/client";
import { Terminal, Code, Cpu, ShieldCheck, Zap } from "lucide-react";

interface SharedEditorProps {
  interviewId: string;
  initialCode?: string;
  language?: string;
}

export default function SharedEditor({ interviewId, initialCode, language = "javascript" }: SharedEditorProps) {
  const supabase = createClient();
  const [lang, setLang] = useState(language);
  const editorRef = useRef<any>(null);
  const providerRef = useRef<any>(null);
  const [status, setStatus] = useState<"connecting" | "synced" | "error">("connecting");

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;

    // 1. Initialize Yjs
    const ydoc = new Y.Doc();
    const ytext = ydoc.getText("monaco");

    // 2. Setup Supabase Realtime Bridge for Yjs
    const channel = supabase.channel(`interview_code_${interviewId}`, {
        config: { broadcast: { self: false } }
    });

    channel
      .on("broadcast", { event: "yjs-update" }, ({ payload }) => {
        // Apply remote update to local Yjs doc
        Y.applyUpdate(ydoc, new Uint8Array(payload));
      })
      .subscribe((status) => {
        if (status === "SUBSCRIBED") setStatus("synced");
      });

    // 3. Listen for local Yjs updates and broadcast them
    ydoc.on("update", (update) => {
      channel.send({
        type: "broadcast",
        event: "yjs-update",
        payload: Array.from(update), // Buffer to array for JSON transport
      });
    });

    // 4. Bind Yjs to Monaco
    const binding = new MonacoBinding(ytext, editor.getModel()!, new Set([editor]), undefined);
    providerRef.current = { ydoc, ytext, binding, channel };

    // Set initial code if empty
    if (initialCode && ytext.toString() === "") {
        ytext.insert(0, initialCode);
    }
  };

  useEffect(() => {
    return () => {
      if (providerRef.current) {
        providerRef.current.binding.destroy();
        providerRef.current.ydoc.destroy();
        supabase.removeChannel(providerRef.current.channel);
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#1e1e1e] rounded-[40px] overflow-hidden border border-white/5 shadow-2xl relative group">
      {/* Editor Header */}
      <div className="flex items-center justify-between px-8 py-5 bg-zinc-900/50 backdrop-blur-md border-b border-white/5">
          <div className="flex items-center space-x-4">
              <div className="p-2.5 bg-primary/10 text-primary rounded-xl">
                  <Code className="w-5 h-5" />
              </div>
              <div>
                  <h4 className="text-[10px] font-black text-white uppercase tracking-[0.2em] italic leading-none mb-1">Collaborative IDE</h4>
                  <div className="flex items-center space-x-2">
                       <span className={`w-1.5 h-1.5 rounded-full ${status === 'synced' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                       <p className="text-[8px] font-black text-gray-500 uppercase tracking-widest">{status === 'synced' ? 'Terminal Synced' : 'Syncing...'}</p>
                  </div>
              </div>
          </div>

          <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-3 bg-black/40 px-4 py-2 rounded-2xl border border-white/5">
                  <Cpu className="w-3 h-3 text-primary" />
                  <select 
                    value={lang}
                    onChange={(e) => setLang(e.target.value)}
                    className="bg-transparent text-[10px] font-black text-gray-400 uppercase tracking-widest outline-none border-none cursor-pointer hover:text-white transition-colors"
                  >
                      <option value="javascript">Javascript</option>
                      <option value="typescript">Typescript</option>
                      <option value="python">Python</option>
                      <option value="java">Java</option>
                  </select>
              </div>
              <button className="flex items-center space-x-2 px-6 py-2.5 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest italic hover:scale-105 transition-all shadow-lg shadow-primary/20 group">
                  <Zap className="w-3 h-3 fill-current group-hover:animate-pulse" />
                  <span>Execute</span>
              </button>
          </div>
      </div>

      {/* Editor Surface */}
      <div className="flex-1 relative">
        <Editor
            height="100%"
            language={lang}
            theme="vs-dark"
            onMount={handleEditorDidMount}
            options={{
                fontSize: 14,
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                fontLigatures: true,
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                smoothScrolling: true,
                cursorBlinking: "smooth",
                cursorSmoothCaretAnimation: "on",
                padding: { top: 20 },
                lineNumbers: "on",
                renderLineHighlight: "all",
                scrollbar: {
                    vertical: "hidden",
                    horizontal: "hidden"
                }
            }}
        />
      </div>

      {/* Persistence Note Overlay */}
      <div className="absolute bottom-6 right-6 p-4 bg-zinc-900/80 backdrop-blur-md rounded-2xl border border-white/10 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500">
          <div className="flex items-center space-x-3">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest italic leading-none">Persistent Snapshotting Enabled</span>
          </div>
      </div>
    </div>
  );
}
