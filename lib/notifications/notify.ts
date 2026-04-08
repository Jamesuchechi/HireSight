import { createClient } from "@/lib/supabase/client";

export type NotificationType =
    | "application_received"
    | "application_status_changed"
    | "new_message"
    | "new_follower"
    | "new_job_from_follow"
    | "interview_scheduled"
    | "screening_completed"
    | "job_expiring"
    | "profile_viewed"
    | "assessment_passed"
    | "system";

export interface NotifyPayload {
    title: string;
    message: string;
    type: NotificationType;
    action_url?: string;
    action_text?: string;
    metadata?: Record<string, any>;
}

/**
 * Creates a notification for a specific user.
 * Can be called from client-side code, API routes, or server actions.
 * 
 * @example
 * await notify(recruiterId, {
 *   title: "New Application Received",
 *   message: `${candidateName} applied for ${jobTitle}`,
 *   type: "application_received",
 *   action_url: `/dashboard/applications/${applicationId}`,
 *   action_text: "Review Application"
 * });
 */
export async function notify(userId: string, payload: NotifyPayload): Promise<void> {
    if (!userId) {
        console.warn("[notify] Skipped: userId is null or undefined");
        return;
    }
    const supabase = createClient();

    const { error } = await supabase.from("notifications").insert({
        user_id: userId,
        title: payload.title,
        message: payload.message,
        type: payload.type,
        action_url: payload.action_url ?? null,
        action_text: payload.action_text ?? null,
        metadata: payload.metadata ?? {},
        is_read: false,
    });

    if (error) {
        console.error("[notify] Failed to create notification:", error.message);
    }
}
