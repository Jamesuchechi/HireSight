import { createClient } from "./client";
import { notify } from "@/lib/notifications/notify";

/**
 * Issues a Neural Badge to a candidate upon successful assessment completion.
 * @param attemptId UUID of the assessment attempt
 */
export async function issueNeuralBadge(attemptId: string) {
    const supabase = createClient();

    // 1. Fetch attempt details
    const { data: attempt, error: aError } = await supabase
        .from("assessment_attempts")
        .select(`
            *,
            assessment:assessments(*)
        `)
        .eq("id", attemptId)
        .single();
    
    if (aError || !attempt) return null;

    // 2. Check if already passed and not previously issued
    if (attempt.status !== "completed" || attempt.score < attempt.assessment.passing_score) {
        return null; 
    }

    // 3. Determine Badge Level
    let level: 'bronze' | 'silver' | 'gold' | 'platinum' = 'bronze';
    const score = Number(attempt.score);
    
    if (score >= 95) level = 'platinum';
    else if (score >= 85) level = 'gold';
    else if (score >= 75) level = 'silver';

    // 4. Create Badge
    const { data: badge, error: bError } = await supabase
        .from("skill_badges")
        .insert({
            user_id: attempt.candidate_id,
            assessment_id: attempt.assessment_id,
            attempt_id: attempt.id,
            skill_name: attempt.assessment.title, // or a specific skill_name field if added later
            badge_level: level,
            score: score,
            metadata: {
                total_points: attempt.total_points,
                proctoring_violations: attempt.metadata?.tab_switch_violations || 0
            }
        })
        .select()
        .single();

    if (bError) {
        console.error("Badge Issuance Failed:", bError);
        return null;
    }

    // 5. Fire assessment_passed notification to the candidate
    await notify(attempt.candidate_id, {
        title: `🏆 ${level.charAt(0).toUpperCase() + level.slice(1)} Badge Earned!`,
        message: `You scored ${score}% and earned a ${level} badge for "${attempt.assessment.title}". View your Neural Trophy Case.`,
        type: "assessment_passed",
        action_url: "/dashboard/achievements",
        action_text: "View Trophy Case",
        metadata: { badge_level: level, skill: attempt.assessment.title, score }
    });

    // 6. Log public activity for the network feed
    const { error: activityError } = await supabase.from("activities").insert({
        user_id: attempt.candidate_id,
        activity_type: "assessment_passed",
        content: {
            assessment_title: attempt.assessment.title,
            badge_level: level,
            score: score
        },
        is_public: true
    });
    if (activityError) console.error("Failed to log activity:", activityError);

    return badge;
}
