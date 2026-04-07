"use client";

import { useState, useEffect } from "react";
import { createClient } from "@/lib/supabase/client";
import { UserPlus, Check, Loader2 } from "lucide-react";
import { notify } from "@/lib/notifications/notify";

interface FollowButtonProps {
    targetUserId: string;
    targetUserName: string;
    currentUserRole?: string; // e.g., 'candidate' or 'recruiter'
    className?: string;
}

export default function FollowButton({ targetUserId, targetUserName, currentUserRole, className = "" }: FollowButtonProps) {
    const supabase = createClient();
    const [isFollowing, setIsFollowing] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [currentUserId, setCurrentUserId] = useState<string | null>(null);

    useEffect(() => {
        const checkFollowState = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                setIsLoading(false);
                return;
            }
            setCurrentUserId(user.id);

            // You can't follow yourself
            if (user.id === targetUserId) {
                setIsLoading(false);
                return;
            }

            const { data } = await supabase
                .from("follows")
                .select("id")
                .eq("follower_id", user.id)
                .eq("following_id", targetUserId)
                .single();

            if (data) {
                setIsFollowing(true);
            }
            setIsLoading(false);
        };
        
        checkFollowState();
    }, [supabase, targetUserId]);

    const handleToggleFollow = async () => {
        if (!currentUserId || isLoading) return;
        setIsLoading(true);

        try {
            if (isFollowing) {
                // Unfollow
                await supabase
                    .from("follows")
                    .delete()
                    .eq("follower_id", currentUserId)
                    .eq("following_id", targetUserId);
                setIsFollowing(false);
            } else {
                // Follow
                await supabase
                    .from("follows")
                    .insert({ follower_id: currentUserId, following_id: targetUserId });
                setIsFollowing(true);

                // Send notification
                const { data: currentUserProfile } = await supabase
                    .from("profiles")
                    .select("full_name")
                    .eq("id", currentUserId)
                    .single();

                await notify(targetUserId, {
                    title: "New Follower Discovered",
                    message: `${currentUserProfile?.full_name || "A user"} added you to their intelligence network.`,
                    type: "new_follower",
                    action_url: `/u/${currentUserId}`,
                    action_text: "View Profile"
                });
            }
        } catch (error) {
            console.error("Failed to toggle follow status:", error);
        } finally {
            setIsLoading(false);
        }
    };

    // Companies shouldn't see follow buttons based on legacy rules (if enforced via prop)
    if (currentUserRole === 'recruiter' || currentUserId === targetUserId) {
        return null; // Implicit logic handles companies not following
    }

    return (
        <button
            onClick={handleToggleFollow}
            disabled={isLoading}
            className={`flex items-center space-x-2 px-4 py-2 rounded-full font-black text-xs uppercase tracking-widest transition-all ${
                isFollowing 
                ? "bg-gray-100 text-gray-500 hover:bg-red-500/10 hover:text-red-500" 
                : "bg-primary text-white hover:scale-105 active:scale-95 shadow-lg shadow-primary/20"
            } ${className}`}
        >
            {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
            ) : isFollowing ? (
                <>
                    <Check className="w-4 h-4" />
                    <span>Following</span>
                </>
            ) : (
                <>
                    <UserPlus className="w-4 h-4" />
                    <span>Follow</span>
                </>
            )}
        </button>
    );
}
