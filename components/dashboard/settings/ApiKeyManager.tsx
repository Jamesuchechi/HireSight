"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Key, Plus, Trash2, Copy, Check, Loader2, Eye, EyeOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface ApiKey {
    id: string;
    name: string;
    key_prefix: string;
    created_at: string;
    last_used_at: string | null;
}

export default function ApiKeyManager() {
    const supabase = createClient();
    const [keys, setKeys] = useState<ApiKey[]>([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [newKey, setNewKey] = useState<string | null>(null);
    const [newName, setNewName] = useState("");
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        fetchKeys();
    }, []);

    const fetchKeys = async () => {
        const { data } = await supabase
            .from("api_keys")
            .select("id, name, key_prefix, created_at, last_used_at")
            .eq("is_active", true)
            .order("created_at", { ascending: false });
        
        if (data) setKeys(data);
        setLoading(false);
    };

    const generateKey = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newName) return;
        setGenerating(true);

        const rawKey = `hs_${Math.random().toString(36).substring(2)}${Math.random().toString(36).substring(2)}`;
        const prefix = rawKey.substring(0, 8);
        
        const { data: { user } } = await supabase.auth.getUser();
        if (user) {
            const { data, error } = await supabase
                .from("api_keys")
                .insert({
                    user_id: user.id,
                    name: newName,
                    key_hash: rawKey, // In production, this should be HASHED
                    key_prefix: prefix
                })
                .select()
                .single();

            if (!error) {
                setNewKey(rawKey);
                setNewName("");
                fetchKeys();
            }
        }
        setGenerating(false);
    };

    const revokeKey = async (id: string) => {
        const { error } = await supabase
            .from("api_keys")
            .update({ is_active: false })
            .eq("id", id);
        
        if (!error) fetchKeys();
    };

    const copyToClipboard = () => {
        if (newKey) {
            navigator.clipboard.writeText(newKey);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (loading) return <div className="p-12 flex justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary" /></div>;

    return (
        <div className="bg-white border border-gray-100 rounded-[40px] p-8 md:p-10 shadow-sm space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                    <div className="p-3 bg-zinc-900 rounded-2xl text-secondary">
                        <Key className="w-5 h-5" />
                    </div>
                    <h3 className="text-xl font-black text-zinc-900 italic uppercase">Neural API Access</h3>
                </div>
            </div>

            {/* Create New Key */}
            <form onSubmit={generateKey} className="flex gap-4 p-6 bg-gray-50 rounded-[32px] border border-gray-100">
                <input 
                    type="text" 
                    placeholder="Key Label (e.g. CI/CD Integration)"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="flex-1 bg-white border border-gray-100 p-4 rounded-2xl text-sm font-bold outline-none focus:border-secondary/30 transition-all"
                />
                <button 
                    disabled={generating || !newName}
                    className="px-8 py-4 bg-zinc-900 text-white rounded-2xl font-black text-[10px] uppercase tracking-widest italic flex items-center space-x-2 disabled:opacity-50"
                >
                    {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4 text-secondary" />}
                    <span>Initialize Access</span>
                </button>
            </form>

            {/* Success Prompt for One-Time Key */}
            <AnimatePresence>
                {newKey && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-secondary/5 border-2 border-secondary/20 rounded-[32px] p-6 space-y-4"
                    >
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-black text-secondary uppercase tracking-widest">Initialization Complete // Copy Key Now</p>
                            <button onClick={() => setNewKey(null)} className="text-gray-400 hover:text-zinc-900 underline text-[10px] font-bold">Dismiss</button>
                        </div>
                        <div className="flex items-center space-x-4 bg-white p-4 rounded-xl border border-secondary/10 shadow-sm">
                            <code className="flex-1 font-mono text-sm font-bold text-zinc-900 break-all">{newKey}</code>
                            <button 
                                onClick={copyToClipboard}
                                className="p-3 bg-secondary text-white rounded-lg hover:scale-105 active:scale-95 transition-all shadow-lg shadow-secondary/20"
                            >
                                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                            </button>
                        </div>
                        <p className="text-[10px] text-secondary/60 font-bold uppercase italic tracking-tighter cursor-default">
                             Warning: This encryption key will not be shown again. Guard it with your life.
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Keys List */}
            <div className="space-y-4">
                {keys.map((key) => (
                    <div key={key.id} className="flex items-center justify-between p-6 border border-gray-50 rounded-[28px] hover:bg-gray-50/50 transition-all group">
                        <div className="space-y-1">
                            <p className="text-sm font-black text-zinc-900 uppercase tracking-widest italic">{key.name}</p>
                            <p className="text-[10px] font-mono font-bold text-gray-400">{key.key_prefix}••••••••••••••••</p>
                            <p className="text-[9px] text-gray-400 font-bold uppercase">EST. {new Date(key.created_at).toLocaleDateString()} // LAST USED: {key.last_used_at ? new Date(key.last_used_at).toLocaleDateString() : 'NEVER'}</p>
                        </div>
                        <button 
                            onClick={() => revokeKey(key.id)}
                            className="p-3 bg-white border border-gray-100 rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all opacity-0 group-hover:opacity-100 shadow-sm"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                ))}
                {keys.length === 0 && (
                    <div className="text-center py-8 text-gray-400 font-bold uppercase text-[10px] tracking-[0.2em] italic">No active neural links found</div>
                )}
            </div>
        </div>
    );
}
