"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { formatDistanceToNow } from "date-fns";
import { MessageSquare, Send, User, Trash2, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Note {
  id: string;
  content: string;
  is_important: boolean;
  created_at: string;
  author_id: string;
  author: {
    full_name: string;
    avatar_url: string | null;
  };
}

export default function ApplicationNotes({ applicationId }: { applicationId: string }) {
  const supabase = createClient();
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [newNote, setNewNote] = useState("");
  const [isImportant, setIsImportant] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchNotes = async () => {
    const { data, error } = await supabase
      .from("application_notes")
      .select(`
        *,
        author:profiles!author_id(full_name, avatar_url)
      `)
      .eq("application_id", applicationId)
      .order("created_at", { ascending: false });

    if (data) setNotes(data as any);
    setLoading(false);
  };

  useEffect(() => {
    fetchNotes();
  }, [applicationId, supabase]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNote.trim() || isSubmitting) return;

    setIsSubmitting(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return;

    const { error } = await supabase
      .from("application_notes")
      .insert({
        application_id: applicationId,
        author_id: user.id,
        content: newNote,
        is_important: isImportant
      });

    if (!error) {
      setNewNote("");
      setIsImportant(false);
      fetchNotes();
    }
    setIsSubmitting(false);
  };

  const deleteNote = async (id: string) => {
    const { error } = await supabase.from("application_notes").delete().eq("id", id);
    if (!error) fetchNotes();
  };

  if (loading) return (
    <div className="flex justify-center p-8">
      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Add Note Form */}
      <form onSubmit={handleSubmit} className="bg-gray-50/50 border border-gray-100 rounded-[32px] p-6 space-y-4">
        <textarea
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Add an internal note about this candidate..."
          className="w-full bg-white border border-gray-100 rounded-2xl p-4 text-sm font-bold focus:outline-none focus:ring-4 focus:ring-primary/5 min-h-[100px] transition-all resize-none shadow-sm"
        />
        <div className="flex items-center justify-between">
          <button 
            type="button"
            onClick={() => setIsImportant(!isImportant)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              isImportant ? "bg-rose-50 text-rose-500 border border-rose-100 shadow-sm shadow-rose-500/10" : "text-gray-400 border border-transparent"
            }`}
          >
            <AlertCircle className="w-4 h-4" />
            <span>Mark as Important</span>
          </button>
          
          <button
            type="submit"
            disabled={!newNote.trim() || isSubmitting}
            className="flex items-center space-x-2 px-6 py-2 bg-zinc-900 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:scale-[1.05] active:scale-[0.95] disabled:opacity-50 transition-all shadow-xl shadow-zinc-900/10"
          >
            {isSubmitting ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>Save Note</span>
                <Send className="w-3 h-3" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Notes List */}
      <div className="space-y-6">
        <AnimatePresence mode="popLayout">
          {notes.map((note, idx) => (
            <motion.div
              key={note.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              layout
              className={`group relative p-6 rounded-[32px] border transition-all ${
                note.is_important 
                ? "bg-rose-50/30 border-rose-100 shadow-sm" 
                : "bg-white border-gray-100 hover:border-primary/20"
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-2xl bg-gray-100 flex items-center justify-center overflow-hidden border border-gray-100 shadow-sm">
                    {note.author.avatar_url ? (
                      <img src={note.author.avatar_url} className="w-full h-full object-cover" alt="" />
                    ) : (
                      <User className="w-5 h-5 text-gray-400" />
                    )}
                  </div>
                  <div>
                    <h5 className="text-sm font-black text-zinc-900 italic tracking-tight">{note.author.full_name}</h5>
                    <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">
                       {formatDistanceToNow(new Date(note.created_at))} ago
                    </p>
                  </div>
                </div>
                
                <button 
                  onClick={() => deleteNote(note.id)}
                  className="p-2 opacity-0 group-hover:opacity-100 text-gray-300 hover:text-rose-500 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <p className="text-sm text-zinc-600 leading-relaxed font-bold italic">
                {note.content}
              </p>

              {note.is_important && (
                <div className="absolute -top-2 -right-2 p-1.5 bg-rose-500 text-white rounded-lg shadow-lg rotate-12">
                   <AlertCircle className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {notes.length === 0 && (
          <div className="text-center py-20 bg-gray-50/30 rounded-[40px] border border-dashed border-gray-100">
            <div className="w-16 h-16 bg-white rounded-full flex items-center justify-center mx-auto mb-4 text-gray-200">
               <MessageSquare className="w-8 h-8" />
            </div>
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest italic">No internal notes yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}
