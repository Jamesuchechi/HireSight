import { NotificationType, NotifyPayload } from "./notify";
import { createClient } from "@/lib/supabase/server";

/**
 * Server-side version using the server client for API route handlers.
 * Use this in Next.js API route handlers (app/api/**).
 */
export async function notifyServer(userId: string, payload: NotifyPayload): Promise<void> {
    const supabase = await createClient();

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
        console.error("[notifyServer] Failed to create notification:", error.message);
    }
}
