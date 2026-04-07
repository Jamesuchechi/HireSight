"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Award, Briefcase, User, Star, MapPin } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";
import FollowButton from "./FollowButton";

interface Activity {
    id: string;
    user_id: string;
    activity_type: string;
    content: Record<string, any>;
    created_at: string;
    profile: {
        full_name: string;
        avatar_url: string;
        role: string;
        location?: string;
    };
}

export default function ActivityFeed() {
    const supabase = createClient();
    const [activities, setActivities] = useState<Activity[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchActivities = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            // Get the list of people the user follows
            const { data: following } = await supabase
                .from("follows")
                .select("following_id")
                .eq("follower_id", user.id);

            const followingIds = following?.map(f => f.following_id) || [];
            
            // Allow users to see their own activities mixed in
            const feedUserIds = [...followingIds, user.id];

            if (feedUserIds.length === 0) {
                setLoading(false);
                return;
            }

            const { data: feed } = await supabase
                .from("activities")
                .select(`
                    id, 
                    user_id, 
                    activity_type, 
                    content, 
                    created_at,
                    profile:profiles!activities_user_id_fkey(full_name, avatar_url, role, location)
                `)
                .in("user_id", feedUserIds)
                .order("created_at", { ascending: false })
                .limit(20);

            if (feed) {
                setActivities(feed as any[]);
            }
            setLoading(false);
        };

        fetchActivities();
    }, [supabase]);

    if (loading) {
        return (
            <div className="flex justify-center p-12">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
        );
    }

    if (activities.length === 0) {
        return (
            <div className="bg-white border-2 border-dashed border-gray-100 rounded-[40px] p-12 text-center space-y-4">
                <Star className="w-12 h-12 text-gray-200 mx-auto" />
                <h3 className="text-xl font-black text-zinc-900 italic tracking-tight">Your Network Feed is Empty</h3>
                <p className="text-sm font-bold text-gray-400">Follow candidates and companies to monitor their latest activities.</p>
            </div>
        );
    }

    const renderActivityIcon = (type: string) => {
        switch (type) {
            case 'assessment_passed': return <Award className="w-5 h-5" />;
            case 'job_posted': return <Briefcase className="w-5 h-5" />;
            default: return <User className="w-5 h-5" />;
        }
    };

    return (
        <div className="space-y-6">
            {activities.map(activity => (
                <div key={activity.id} className="bg-white border border-gray-100 rounded-[32px] p-8 shadow-sm flex gap-6 hover:shadow-md transition-shadow group">
                    <Link href={`/u/${activity.user_id}`} className="shrink-0">
                        <div className="w-16 h-16 bg-gray-50 rounded-2xl border border-gray-100 overflow-hidden flex items-center justify-center font-black text-primary italic text-xl group-hover:scale-105 transition-transform">
                            {activity.profile?.avatar_url ? (
                                <img src={activity.profile.avatar_url} alt="" className="w-full h-full object-cover" />
                            ) : (
                                <span>{activity.profile?.full_name?.charAt(0) || "?"}</span>
                            )}
                        </div>
                    </Link>
                    
                    <div className="flex-1 space-y-2">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <Link href={`/u/${activity.user_id}`} className="text-lg font-black text-zinc-900 italic hover:text-primary transition-colors">
                                    {activity.profile?.full_name || "Unknown"}
                                </Link>
                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 flex items-center gap-2 mt-1">
                                    {activity.profile?.role === 'company' ? 'Corporate' : 'Candidate'}
                                    {activity.profile?.location && (
                                        <>
                                            <span>•</span>
                                            <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{activity.profile.location}</span>
                                        </>
                                    )}
                                </p>
                            </div>
                            <span className="text-[10px] font-black uppercase tracking-widest text-gray-300 whitespace-nowrap">
                                {formatDistanceToNow(new Date(activity.created_at))} ago
                            </span>
                        </div>

                        {/* Activity Content Rendering */}
                        <div className="bg-gray-50/50 border border-gray-50 rounded-[20px] p-5 mt-4">
                            <div className="flex items-center gap-3 mb-2 text-primary">
                                {renderActivityIcon(activity.activity_type)}
                                <span className="text-[10px] font-black uppercase tracking-widest italic decoration-2 underline decoration-primary/20">
                                    {activity.activity_type === 'assessment_passed' ? 'Skill Verification Earned' : 
                                     activity.activity_type === 'job_posted' ? 'New Mission Deployed' : activity.activity_type}
                                </span>
                            </div>

                            {activity.activity_type === 'assessment_passed' && (
                                <div>
                                    <p className="text-sm font-bold text-gray-600 italic">
                                        Earned a <span className="text-primary font-black">{activity.content.badge_level}</span> badge for <span className="font-black">"{activity.content.assessment_title}"</span> with a score of {activity.content.score}%.
                                    </p>
                                </div>
                            )}

                            {activity.activity_type === 'job_posted' && (
                                <div>
                                    <p className="text-sm font-bold text-gray-600 italic">
                                        Now hiring for <span className="text-primary font-black">"{activity.content.job_title}"</span> in {activity.content.location}.
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
