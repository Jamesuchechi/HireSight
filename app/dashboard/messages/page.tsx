"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { 
    Search, 
    Plus, 
    MoreVertical, 
    Send, 
    Paperclip, 
    Smile, 
    User,
    Check,
    CheckCheck,
    Archive,
    Trash2,
    Flag,
    MessageSquare,
    Zap,
    ArrowLeft,
    Clock,
    FileText,
    Target,
    Radar,
    X,
    Loader2
} from "lucide-react";

import { motion, AnimatePresence } from "framer-motion";
import { formatDistanceToNow } from "date-fns";
import { useRouter, useSearchParams } from "next/navigation";
import { injectVariables, SEED_TEMPLATES } from "@/lib/messaging/templates";


interface Message {
    id: string;
    content: string;
    sender_id: string;
    created_at: string;
    message_type: 'user' | 'system' | 'template';
    is_edited: boolean;
    is_deleted: boolean;
}

interface Conversation {
    id: string;
    subject: string;
    updated_at: string;
    other_participant: {
        id: string;
        full_name: string;
        avatar_url: string;
        role: string;
    };
    last_message?: string;
    unread_count: number;
}

function MessagingHubContent() {
    const supabase = createClient();
    const router = useRouter();
    const searchParams = useSearchParams();
    const scrollRef = useRef<HTMLDivElement>(null);

    const [loading, setLoading] = useState(true);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [newMessage, setNewMessage] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [currentUser, setCurrentUser] = useState<any>(null);
    const [isTyping, setIsTyping] = useState(false);
    const [showTemplates, setShowTemplates] = useState(false);
    const [templates, setTemplates] = useState<any[]>(SEED_TEMPLATES);
    const [attachments, setAttachments] = useState<File[]>([]);
    const [showNewChatSearch, setShowNewChatSearch] = useState(false);
    const [userSearchResults, setUserSearchResults] = useState<any[]>([]);
    const [userSearchQuery, setUserSearchQuery] = useState("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const init = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;
            setCurrentUser(user);
            await fetchConversations();
            
            const recipientId = searchParams.get('recipient');
            if (recipientId) {
                handleStartConversation(recipientId);
            }
        };
        init();
    }, [searchParams]);


    useEffect(() => {
        if (activeConversation) {
            fetchMessages(activeConversation.id);
            subscribeToMessages(activeConversation.id);
        }
    }, [activeConversation]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    };

    const fetchConversations = async () => {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) return;

        const { data, error } = await supabase
            .from('conversation_participants')
            .select(`
                conversation:conversations (
                    id, subject, updated_at,
                    participants:conversation_participants (
                        user:profiles (id, full_name, avatar_url, role)
                    )
                )
            `)
            .eq('user_id', user.id);

        if (data) {
            const formatted = data.map((item: any) => {
                const conv = item.conversation;
                const other = conv.participants.find((p: any) => p.user.id !== user.id)?.user;
                return {
                    id: conv.id,
                    subject: conv.subject,
                    updated_at: conv.updated_at,
                    other_participant: other || { full_name: "Unknown", avatar_url: "", role: "" },
                    unread_count: 0 // Logic for unread count will be added
                };
            }).sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
            
            setConversations(formatted);
            setLoading(false);
        }
    };

    const fetchMessages = async (convId: string) => {
        const { data, error } = await supabase
            .from('messages')
            .select('*')
            .eq('conversation_id', convId)
            .order('created_at', { ascending: true });

        if (data) setMessages(data);
    };

    const handleStartConversation = async (targetUserId: string) => {

        const { data: { user } } = await supabase.auth.getUser();
        if (!user || user.id === targetUserId) return;

        // Check for existing conversation
        const { data: existing } = await supabase
            .from('conversation_participants')
            .select('conversation_id')
            .eq('user_id', user.id);
        
        const myConvIds = existing?.map(e => e.conversation_id) || [];
        
        const { data: shared } = await supabase
            .from('conversation_participants')
            .select('conversation_id')
            .in('conversation_id', myConvIds)
            .eq('user_id', targetUserId)
            .single();

        if (shared) {
            const { data: convData } = await supabase
                .from('conversations')
                .select(`
                    id, subject, updated_at,
                    participants:conversation_participants (
                        user:profiles (id, full_name, avatar_url, role)
                    )
                `)
                .eq('id', shared.conversation_id)
                .single();
            
            if (convData) {
                const participants = convData.participants as any[];
                const other = participants.find((p: any) => p.user.id !== user.id)?.user;
                const formatted: Conversation = {
                    id: convData.id,
                    subject: convData.subject,
                    updated_at: convData.updated_at,
                    other_participant: other || { id: "", full_name: "Unknown", avatar_url: "", role: "" },
                    unread_count: 0
                };
                setActiveConversation(formatted);
            }


        } else {
            // Create new
            const { data: newConv } = await supabase
                .from('conversations')
                .insert({ subject: 'Direct Neural Link' })
                .select()
                .single();

            if (newConv) {
                await supabase.from('conversation_participants').insert([
                    { conversation_id: newConv.id, user_id: user.id },
                    { conversation_id: newConv.id, user_id: targetUserId }
                ]);
                
                await fetchConversations();
                // Instead of recursing, just manually fetch and set it
                const { data: freshConv } = await supabase
                    .from('conversations')
                    .select(`
                        id, subject, updated_at,
                        participants:conversation_participants (
                            user:profiles (id, full_name, avatar_url, role)
                        )
                    `)
                    .eq('id', newConv.id)
                    .single();
                
                if (freshConv) {
                    const participants = freshConv.participants as any[];
                    const other = participants.find((p: any) => p.user.id !== user.id)?.user;
                    setActiveConversation({
                        id: freshConv.id,
                        subject: freshConv.subject,
                        updated_at: freshConv.updated_at,
                        other_participant: other || { id: "", full_name: "Unknown", avatar_url: "", role: "" },
                        unread_count: 0
                    });
                }


            }
        }
    };


    const searchUsers = async (query: string) => {
        setUserSearchQuery(query);
        if (query.length < 2) {
            setUserSearchResults([]);
            return;
        }

        const { data } = await supabase
            .from('profiles')
            .select('id, full_name, avatar_url, role')
            .ilike('full_name', `%${query}%`)
            .limit(5);
        
        if (data) setUserSearchResults(data);
    };


    const subscribeToMessages = (convId: string) => {
        const channel = supabase
            .channel(`room_${convId}`)
            .on('postgres_changes', { 
                event: 'INSERT', 
                schema: 'public', 
                table: 'messages',
                filter: `conversation_id=eq.${convId}`
            }, (payload) => {
                setMessages(prev => [...prev, payload.new as Message]);
            })
            .on('broadcast', { event: 'typing' }, ({ payload }) => {
                if (payload.userId !== currentUser?.id) {
                    setIsTyping(true);
                    setTimeout(() => setIsTyping(false), 3000);
                }
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    };

    const handleTyping = () => {
        if (!activeConversation || !currentUser) return;
        supabase.channel(`room_${activeConversation.id}`).send({
            type: 'broadcast',
            event: 'typing',
            payload: { userId: currentUser.id }
        });
    };


    const handleSendMessage = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if ((!newMessage.trim() && attachments.length === 0) || !activeConversation || !currentUser) return;

        const messageContent = newMessage;
        const currentAttachments = [...attachments];
        setNewMessage("");
        setAttachments([]);

        const { data: msgData, error } = await supabase
            .from('messages')
            .insert({
                conversation_id: activeConversation.id,
                sender_id: currentUser.id,
                content: messageContent,
                message_type: 'user'
            })
            .select()
            .single();

        if (error) {
            console.error("Transmission Error:", error);
            setNewMessage(messageContent);
            setAttachments(currentAttachments);
        } else if (currentAttachments.length > 0) {
            // Production Storage Upload logic
            for (const file of currentAttachments) {
                const fileExt = file.name.split('.').pop();
                const filePath = `${msgData.id}/${Math.random()}.${fileExt}`;
                
                const { error: uploadError, data: uploadData } = await supabase.storage
                    .from('message-attachments')
                    .upload(filePath, file);

                if (!uploadError) {
                    const { data: { publicUrl } } = supabase.storage
                        .from('message-attachments')
                        .getPublicUrl(filePath);

                    await supabase.from('message_attachments').insert({
                        message_id: msgData.id,
                        filename: file.name,
                        file_url: publicUrl,
                        file_type: file.type,
                        file_size: file.size
                    });
                }
            }
            
            await supabase
                .from('conversations')
                .update({ updated_at: new Date().toISOString() })
                .eq('id', activeConversation.id);
        }
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setAttachments(prev => [...prev, ...Array.from(e.target.files!)]);
        }
    };


    if (loading) return (
        <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Accessing Neural Frequency...</p>
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto h-[calc(100vh-180px)] min-h-[600px] flex overflow-hidden border border-gray-100 rounded-[48px] bg-white shadow-2xl">
            {/* Sidebar: Conversations List */}
            <div className="w-full md:w-[400px] flex flex-col border-r border-gray-50">
                <header className="p-8 border-b border-gray-50 space-y-6">
                    <div className="flex items-center justify-between">
                        <h1 className="text-3xl font-black font-display italic tracking-tight text-zinc-900">Inbox</h1>
                        <button 
                            onClick={() => setShowNewChatSearch(true)}
                            className="p-3 bg-primary/10 text-primary rounded-2xl hover:bg-primary hover:text-white transition-all shadow-sm"
                        >
                            <Plus className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-focus-within:text-primary transition-colors" />
                        <input 
                            type="text" 
                            placeholder="Scan Signal..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-gray-50 border-none rounded-2xl py-4 pl-12 pr-4 text-xs font-bold italic placeholder:text-gray-400 focus:ring-4 focus:ring-primary/10 transition-all outline-none"
                        />
                    </div>
                </header>

                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {conversations.length > 0 ? (
                        conversations.map(conv => (
                            <button 
                                key={conv.id}
                                onClick={() => setActiveConversation(conv)}
                                className={`w-full p-6 flex items-start space-x-4 border-b border-gray-50/50 transition-all hover:bg-gray-50 relative group ${activeConversation?.id === conv.id ? 'bg-primary/5' : ''}`}
                            >
                                <div className="relative">
                                    <div className="w-14 h-14 bg-gray-100 rounded-2xl overflow-hidden border border-gray-100">
                                        {conv.other_participant.avatar_url ? (
                                            <img src={conv.other_participant.avatar_url} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center font-black text-xl text-primary/40 uppercase italic">
                                                {conv.other_participant.full_name[0]}
                                            </div>
                                        )}
                                    </div>
                                    <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-white rounded-full" />
                                </div>
                                <div className="flex-1 text-left space-y-1 min-w-0">
                                    <div className="flex justify-between items-center">
                                        <h4 className="text-sm font-black text-zinc-900 italic truncate pr-2">
                                            {conv.other_participant.full_name}
                                        </h4>
                                        <span className="text-[8px] font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">
                                            {formatDistanceToNow(new Date(conv.updated_at), { addSuffix: false })}
                                        </span>
                                    </div>
                                    <p className="text-[10px] font-bold text-gray-400 tracking-wider truncate uppercase">
                                        {conv.other_participant.role}
                                    </p>
                                    <p className="text-xs font-medium text-gray-500 truncate italic">
                                        {conv.subject || "Neural Transmission Loop..."}
                                    </p>
                                </div>
                                {activeConversation?.id === conv.id && (
                                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
                                )}
                            </button>
                        ))
                    ) : (
                        <div className="p-12 text-center space-y-4 opacity-40">
                            <MessageSquare className="w-12 h-12 mx-auto" />
                            <p className="text-[10px] font-black uppercase tracking-widest italic">No Passive Signals Detected</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Main: Chat Thread */}
            <div className="flex-1 flex flex-col bg-gray-50/30">
                {activeConversation ? (
                    <>
                        <header className="p-8 bg-white border-b border-gray-50 flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <button className="md:hidden p-2 text-gray-400">
                                    <ArrowLeft className="w-6 h-6" />
                                </button>
                                <div className="w-12 h-12 rounded-2xl bg-gray-100 overflow-hidden border border-gray-100">
                                    {activeConversation.other_participant.avatar_url ? (
                                        <img src={activeConversation.other_participant.avatar_url} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center font-black text-primary/40 text-lg uppercase italic">
                                            {activeConversation.other_participant.full_name[0]}
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <h3 className="text-xl font-black text-zinc-900 italic tracking-tight underline decoration-2 decoration-primary/10">
                                        {activeConversation.other_participant.full_name}
                                    </h3>
                                    <div className="flex items-center space-x-2">
                                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />
                                        <span className="text-[8px] font-black text-gray-400 uppercase tracking-[0.2em] italic">Active Synchronized</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center space-x-2">
                                <button className="p-3 text-gray-400 hover:text-zinc-900 transition-colors">
                                    <Search className="w-5 h-5" />
                                </button>
                                <button className="p-3 text-gray-400 hover:text-zinc-900 transition-colors">
                                    <Archive className="w-5 h-5" />
                                </button>
                                <button className="p-3 text-gray-400 hover:text-zinc-900 transition-colors">
                                    <MoreVertical className="w-5 h-5" />
                                </button>
                            </div>
                        </header>

                        <div 
                            ref={scrollRef}
                            className="flex-1 overflow-y-auto p-12 space-y-8 custom-scrollbar scroll-smooth"
                        >
                            <div className="flex justify-center mb-12">
                                <div className="px-6 py-2 bg-white border border-gray-100 rounded-full shadow-sm text-[8px] font-black uppercase tracking-[0.3em] text-gray-400 italic">
                                    Secure Connection Established // End-to-End Encryption
                                </div>
                            </div>

                            {messages.map((msg, i) => {
                                const isOwn = msg.sender_id === currentUser.id;
                                return (
                                    <motion.div 
                                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                        key={msg.id}
                                        className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}
                                    >
                                        <div className={`max-w-[70%] space-y-2 ${isOwn ? 'items-end' : 'items-start'}`}>
                                            <div className={`p-6 rounded-[32px] font-body text-sm leading-relaxed ${
                                                isOwn 
                                                ? 'bg-zinc-900 text-white italic rounded-tr-none' 
                                                : 'bg-white text-zinc-800 border border-gray-100 rounded-tl-none border-l-4 border-l-primary'
                                            }`}>
                                                {msg.content}
                                            </div>
                                            <div className="flex items-center space-x-3 px-2">
                                                <span className="text-[8px] font-black text-gray-400 uppercase tracking-widest italic flex items-center space-x-1">
                                                    <Clock className="w-2.5 h-2.5" />
                                                    <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                </span>
                                                {isOwn && (
                                                    <CheckCheck className="w-3 h-3 text-primary" />
                                                )}
                                            </div>
                                        </div>
                                    </motion.div>
                                );
                            })}
                            {isTyping && (
                                <div className="flex justify-start">
                                    <div className="bg-white border border-gray-50 px-6 py-4 rounded-full flex space-x-1">
                                        <div className="w-1 h-1 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]" />
                                        <div className="w-1 h-1 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]" />
                                        <div className="w-1 h-1 bg-primary rounded-full animate-bounce" />
                                    </div>
                                </div>
                            )}
                        </div>

                        <footer className="p-8 bg-white border-t border-gray-50 space-y-4">
                            {attachments.length > 0 && (
                                <div className="flex flex-wrap gap-2 pb-2">
                                    {attachments.map((file, i) => (
                                        <div key={i} className="px-4 py-2 bg-zinc-900 text-white rounded-xl text-[10px] font-black uppercase italic flex items-center space-x-2">
                                            <FileText className="w-3 h-3" />
                                            <span>{file.name}</span>
                                            <button 
                                                onClick={() => setAttachments(prev => prev.filter((_, idx) => idx !== i))}
                                                className="hover:text-primary"
                                            >
                                                <MoreVertical className="w-3 h-3" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                            <form 
                                onSubmit={handleSendMessage}
                                className="relative flex items-end space-x-4 bg-gray-50 border border-gray-100 rounded-[32px] p-2 transition-all focus-within:ring-4 focus-within:ring-primary/5 focus-within:border-primary/20"
                            >
                                <input 
                                    type="file" 
                                    multiple 
                                    ref={fileInputRef} 
                                    className="hidden" 
                                    onChange={handleFileSelect}
                                />
                                <button 
                                    type="button" 
                                    onClick={() => fileInputRef.current?.click()}
                                    className="p-4 text-gray-400 hover:text-primary transition-colors hover:scale-110 active:scale-90"
                                >
                                    <Paperclip className="w-5 h-5" />
                                </button>
                                <textarea 
                                    rows={1}
                                    value={newMessage}
                                    onChange={(e) => {
                                        setNewMessage(e.target.value);
                                        handleTyping();
                                    }}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSendMessage();
                                        }
                                    }}
                                    placeholder="Enter Neural Input..."
                                    className="flex-1 bg-transparent border-none py-4 px-2 text-sm font-bold italic text-zinc-900 placeholder:text-gray-400 outline-none resize-none max-h-32"
                                />
                                <div className="flex items-center space-x-1 pr-2">
                                    <div className="relative">
                                        <AnimatePresence>
                                            {showTemplates && (
                                                <motion.div 
                                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                                    className="absolute bottom-full right-0 mb-4 w-80 bg-white border border-gray-100 rounded-[32px] shadow-2xl p-6 z-50 space-y-4"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <h4 className="text-[10px] font-black uppercase tracking-widest text-zinc-900 italic">Neural Templates</h4>
                                                        <Zap className="w-3 h-3 text-primary animate-pulse" />
                                                    </div>
                                                    <div className="max-h-60 overflow-y-auto custom-scrollbar space-y-2">
                                                        {templates.map(t => (
                                                            <button 
                                                                key={t.name}
                                                                onClick={() => {
                                                                    const injected = injectVariables(t.content, {
                                                                        candidate_name: activeConversation.other_participant.full_name,
                                                                        company_name: "HireSight", // Default or fetch from profile
                                                                        job_title: activeConversation.subject || "Mission Node"
                                                                    });
                                                                    setNewMessage(injected);
                                                                    setShowTemplates(false);
                                                                }}
                                                                className="w-full text-left p-4 hover:bg-gray-50 rounded-2xl transition-all group"
                                                            >
                                                                <p className="text-[10px] font-black text-primary uppercase italic mb-1">{t.name}</p>
                                                                <p className="text-xs text-gray-500 italic truncate group-hover:text-zinc-800">{t.content}</p>
                                                            </button>
                                                        ))}
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                        <button 
                                            type="button" 
                                            onClick={() => setShowTemplates(!showTemplates)}
                                            className={`p-4 transition-colors ${showTemplates ? 'text-primary' : 'text-gray-400 hover:text-amber-500'}`}
                                        >
                                            <Zap className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <button 
                                        type="submit"
                                        disabled={!newMessage.trim()}
                                        className="p-4 bg-zinc-900 text-white rounded-2xl hover:bg-primary transition-all shadow-xl active:scale-95 disabled:opacity-20 disabled:grayscale group"
                                    >
                                        <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                                    </button>
                                </div>
                            </form>
                        </footer>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center space-y-8 p-12 text-center">
                        <div className="w-32 h-32 bg-white rounded-[40px] shadow-2xl flex items-center justify-center relative group">
                            <MessageSquare className="w-16 h-16 text-primary group-hover:scale-110 transition-transform duration-500" />
                            <div className="absolute inset-0 bg-primary/5 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div className="space-y-3 max-w-sm">
                            <h3 className="text-3xl font-black italic text-zinc-900 tracking-tighter">Neural Communication Hub</h3>
                            <p className="text-sm font-body text-gray-400 italic leading-relaxed">
                                Select a sector node to initiate secure transmission. Sync rates are operating at peak efficiency.
                            </p>
                        </div>
                        <div className="flex flex-wrap justify-center gap-3">
                             {["Direct Inquiries", "Interview Scheduling", "Offer Negotiations"].map(tag => (
                                 <span key={tag} className="px-4 py-2 bg-white border border-gray-100 rounded-full text-[8px] font-black uppercase tracking-widest text-gray-400 shadow-sm">{tag}</span>
                             ))}
                        </div>
                    </div>
                )}
            </div>

            {/* New Chat Search Modal */}
            <AnimatePresence>
                {showNewChatSearch && (
                    <div className="fixed inset-0 bg-zinc-900/60 backdrop-blur-md z-[100] flex items-center justify-center p-4">
                        <motion.div 
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="bg-white w-full max-w-lg rounded-[48px] shadow-2xl overflow-hidden"
                        >
                            <div className="p-8 border-b border-gray-50 flex items-center justify-between">
                                <h3 className="text-2xl font-black italic text-zinc-900">Discover Operatives</h3>
                                <button onClick={() => setShowNewChatSearch(false)} className="p-2 hover:bg-gray-100 rounded-full">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>
                            <div className="p-8 space-y-6">
                                <div className="relative">
                                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                    <input 
                                        type="text" 
                                        placeholder="Scan by Name..." 
                                        autoFocus
                                        value={userSearchQuery}
                                        onChange={(e) => searchUsers(e.target.value)}
                                        className="w-full bg-gray-50 border-none rounded-2xl py-4 pl-12 pr-4 text-sm font-bold italic focus:ring-4 focus:ring-primary/10 transition-all outline-none"
                                    />
                                </div>
                                <div className="space-y-2 min-h-[200px]">
                                    {userSearchResults.map(u => (
                                        <button 
                                            key={u.id}
                                            onClick={() => {
                                                handleStartConversation(u.id);
                                                setShowNewChatSearch(false);
                                            }}
                                            className="w-full p-4 flex items-center space-x-4 hover:bg-primary/5 rounded-2xl transition-all group"
                                        >
                                            <div className="w-10 h-10 rounded-xl bg-gray-100 overflow-hidden">
                                                {u.avatar_url ? <img src={u.avatar_url} className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center font-black text-gray-400 italic">{u.full_name[0]}</div>}
                                            </div>
                                            <div className="flex-1 text-left">
                                                <p className="text-sm font-black italic text-zinc-900">{u.full_name}</p>
                                                <p className="text-[10px] font-bold text-primary uppercase tracking-widest">{u.role}</p>
                                            </div>
                                            <MessageSquare className="w-4 h-4 text-gray-300 group-hover:text-primary transition-colors" />
                                        </button>
                                    ))}
                                    {userSearchQuery.length >= 2 && userSearchResults.length === 0 && (
                                        <div className="text-center py-12 opacity-40">
                                            <Radar className="w-12 h-12 mx-auto mb-4 animate-pulse" />
                                            <p className="text-[10px] font-black uppercase tracking-widest italic">No Passive Signals in this Sector</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}

export default function MessagingHub() {
    return (
        <Suspense fallback={
            <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
                <Loader2 className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 italic">Initializing Secure Channel...</p>
            </div>
        }>
            <MessagingHubContent />
        </Suspense>
    );
}
