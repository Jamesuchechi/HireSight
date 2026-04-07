"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { Users, Radar, UserPlus, BrainCircuit, Search, ChevronRight } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Link from "next/link";
import ActivityFeed from "@/components/network/ActivityFeed";
import FollowButton from "@/components/network/FollowButton";

export default function NetworkPage() {
    const supabase = createClient();
    const [activeTab, setActiveTab] = useState<"feed" | "connections" | "discovery">("feed");
    const [connectionsTab, setConnectionsTab] = useState<"following" | "followers">("following");
    
    const [following, setFollowing] = useState<any[]>([]);
    const [followers, setFollowers] = useState<any[]>([]);
    const [suggestions, setSuggestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [currentUser, setCurrentUser] = useState<any>(null);

    useEffect(() => {
        const fetchNetworkData = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;
            setCurrentUser(user);

            // Fetch Following Data
            const { data: followingData } = await supabase
                .from("follows")
                .select(`
                    id, 
                    following_id,
                    profile:profiles!follows_following_id_fkey(id, full_name, avatar_url, role, location, headline)
                `)
                .eq("follower_id", user.id);

            // Fetch Followers Data
            const { data: followersData } = await supabase
                .from("follows")
                .select(`
                    id, 
                    follower_id,
                    profile:profiles!follows_follower_id_fkey(id, full_name, avatar_url, role, location, headline)
                `)
                .eq("following_id", user.id);

            // Basic Discovery (Just grabbing other companies or candidates for now, exclude self and already followed)
            const followedIds = followingData?.map((f: any) => f.following_id) || [];
            const excludeIds = [...followedIds, user.id];

            const { data: discoveryData } = await supabase
                .from("profiles")
                .select("id, full_name, avatar_url, role, location, headline")
                .not("id", "in", `(${excludeIds.join(',')})`)
                .limit(10);

            if (followingData) setFollowing(followingData);
            if (followersData) setFollowers(followersData);
            if (discoveryData) setSuggestions(discoveryData);
            
            setLoading(false);
        };

        fetchNetworkData();
    }, [supabase, activeTab]);

    return (
        <div className="max-w-7xl mx-auto space-y-12 pb-24">
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                        <div className="p-3 bg-primary/10 text-primary rounded-[20px]">
                            <Radar className="w-6 h-6" />
                        </div>
                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.2em] italic underline decoration-2 decoration-primary/20">
                            Neural Sync
                        </span>
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter">
                        Command <span className="text-primary tracking-normal font-body">Network</span>
                    </h1>
                </div>

                {/* Main Navigation Tabs */}
                <div className="flex bg-gray-100 p-1.5 rounded-[24px]">
                    {[
                        { id: "feed", label: "Intelligence Feed", icon: <Radar className="w-4 h-4" /> },
                        { id: "connections", label: "Connections", icon: <Users className="w-4 h-4" /> },
                        { id: "discovery", label: "Discovery", icon: <Search className="w-4 h-4" /> }
                    ].map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`flex items-center space-x-2 px-6 py-3 rounded-[20px] text-[10px] font-black uppercase tracking-widest transition-all ${
                                activeTab === tab.id 
                                    ? "bg-white text-zinc-900 shadow-sm" 
                                    : "text-gray-400 hover:text-gray-600"
                            }`}
                        >
                            {tab.icon}
                            <span className="hidden sm:inline">{tab.label}</span>
                        </button>
                    ))}
                </div>
            </header>

            <AnimatePresence mode="wait">
                {activeTab === "feed" && (
                    <motion.div
                        key="feed"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="grid grid-cols-1 lg:grid-cols-12 gap-12"
                    >
                        <div className="lg:col-span-8">
                            <ActivityFeed />
                        </div>
                        <div className="lg:col-span-4 space-y-8">
                            <div className="bg-zinc-900 text-white border border-gray-800 rounded-[40px] p-8 space-y-6 relative overflow-hidden">
                                <div className="absolute right-0 top-0 w-32 h-32 bg-primary/20 blur-[50px] rounded-full pointer-events-none" />
                                <BrainCircuit className="w-8 h-8 text-primary mb-4" />
                                <h3 className="text-xl font-black italic tracking-tighter">Network Insights</h3>
                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest leading-relaxed">
                                    Your intelligence feed monitors milestones (like assessments passed) and deployed missions (new jobs) across your verified connections.
                                </p>
                            </div>
                        </div>
                    </motion.div>
                )}

                {activeTab === "connections" && (
                    <motion.div
                        key="connections"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="space-y-8"
                    >
                        <div className="flex space-x-4 border-b border-gray-100 pb-4">
                            <button
                                onClick={() => setConnectionsTab("following")}
                                className={`text-xs font-black uppercase tracking-widest px-4 py-2 rounded-full transition-all ${
                                    connectionsTab === "following" ? "bg-primary text-white" : "text-gray-400 hover:text-zinc-900"
                                }`}
                            >
                                Following ({following.length})
                            </button>
                            <button
                                onClick={() => setConnectionsTab("followers")}
                                className={`text-xs font-black uppercase tracking-widest px-4 py-2 rounded-full transition-all ${
                                    connectionsTab === "followers" ? "bg-primary text-white" : "text-gray-400 hover:text-zinc-900"
                                }`}
                            >
                                Followers ({followers.length})
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {(connectionsTab === "following" ? following : followers).map((conn: any) => {
                                const profile = conn.profile;
                                if (!profile) return null;
                                return (
                                    <div key={conn.id} className="bg-white border border-gray-100 rounded-[32px] p-6 flex flex-col justify-between group hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all">
                                        <div className="space-y-4 mb-6">
                                            <div className="flex items-center justify-between">
                                                <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 overflow-hidden flex items-center justify-center font-black text-xl text-primary italic">
                                                    {profile.avatar_url ? (
                                                        <img src={profile.avatar_url} className="w-full h-full object-cover" />
                                                    ) : (
                                                        <span>{profile.full_name?.charAt(0) || "?"}</span>
                                                    )}
                                                </div>
                                                <span className="px-3 py-1 bg-gray-50 text-gray-400 text-[8px] font-black uppercase tracking-widest rounded-lg border border-gray-100">
                                                    {profile.role}
                                                </span>
                                            </div>
                                            <div>
                                                <Link href={`/u/${profile.id}`} className="text-lg font-black text-zinc-900 italic hover:text-primary transition-colors line-clamp-1">
                                                    {profile.full_name}
                                                </Link>
                                                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest line-clamp-2 mt-1">
                                                    {profile.headline || profile.location || "Active Node"}
                                                </p>
                                            </div>
                                        </div>
                                        {/* You can only unfollow if you're on the 'Following' tab. If you're on 'Followers', you might want to follow back. */}
                                        <FollowButton 
                                            targetUserId={profile.id} 
                                            targetUserName={profile.full_name} 
                                            className="w-full justify-center py-3"
                                        />
                                    </div>
                                );
                            })}
                            
                            {(connectionsTab === "following" ? following : followers).length === 0 && (
                                <div className="col-span-3 text-center py-12">
                                    <p className="text-xs font-black text-gray-300 uppercase tracking-widest">No connections found in this sector.</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {activeTab === "discovery" && (
                    <motion.div
                        key="discovery"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="space-y-8"
                    >
                        <div className="bg-white border border-gray-100 rounded-[32px] p-6 shadow-sm flex items-center justify-between">
                            <div className="flex items-center space-x-3">
                                <UserPlus className="w-5 h-5 text-emerald-500" />
                                <span className="text-[10px] font-black uppercase tracking-[0.2em] italic text-zinc-900">Recommended Targets</span>
                            </div>
                            <button onClick={() => window.location.reload()} className="text-[10px] font-black text-gray-400 uppercase tracking-widest hover:text-primary transition-colors">
                                Refresh Scan
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {suggestions.map((profile: any) => (
                                <div key={profile.id} className="bg-white border border-gray-100 rounded-[32px] p-6 flex flex-col justify-between group hover:border-primary/20 hover:shadow-xl hover:shadow-primary/5 transition-all">
                                    <div className="space-y-4 mb-6">
                                        <div className="flex items-center justify-between">
                                            <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 overflow-hidden flex items-center justify-center font-black text-xl text-primary italic">
                                                {profile.avatar_url ? (
                                                    <img src={profile.avatar_url} className="w-full h-full object-cover" />
                                                ) : (
                                                    <span>{profile.full_name?.charAt(0) || "?"}</span>
                                                )}
                                            </div>
                                            <span className="px-3 py-1 bg-gray-50 text-gray-400 text-[8px] font-black uppercase tracking-widest rounded-lg border border-gray-100">
                                                {profile.role}
                                            </span>
                                        </div>
                                        <div>
                                            <Link href={`/u/${profile.id}`} className="text-lg font-black text-zinc-900 italic hover:text-primary transition-colors line-clamp-1">
                                                {profile.full_name}
                                            </Link>
                                            <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest line-clamp-2 mt-1">
                                                {profile.headline || profile.location || "Active Node"}
                                            </p>
                                        </div>
                                    </div>
                                    <FollowButton 
                                        targetUserId={profile.id} 
                                        targetUserName={profile.full_name} 
                                        className="w-full justify-center py-3"
                                    />
                                </div>
                            ))}
                            
                            {suggestions.length === 0 && (
                                <div className="col-span-3 text-center py-12">
                                    <p className="text-xs font-black text-gray-300 uppercase tracking-widest">Scanning complete. No new targets discovered.</p>
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
