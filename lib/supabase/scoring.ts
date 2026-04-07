import { createClient } from "./client";

/**
 * Calculates and updates the combined neural match score for a job application.
 * Formula: (AI_Resume_Match * 0.4) + (Technical_Assessment_Score * 0.6)
 * @param applicationId UUID of the job application
 */
export async function updateCombinedNeuralScore(applicationId: string) {
    const supabase = createClient();

    // 1. Fetch current application (AI score) and all completed assessments
    const { data: application, error: aError } = await supabase
        .from("job_applications")
        .select("match_score, candidate_id, job_id")
        .eq("id", applicationId)
        .single();
    
    if (aError || !application) return;

    // 2. Fetch assessment attempts for this candidate and job
    const { data: attempts } = await supabase
        .from("assessment_attempts")
        .select("score")
        .eq("candidate_id", application.candidate_id)
        .eq("job_application_id", applicationId)
        .eq("status", "completed");

    let finalScore = application.match_score || 0;

    if (attempts && attempts.length > 0) {
        // Average assessment score
        const avgAssessmentScore = attempts.reduce((acc, curr) => acc + (Number(curr.score) || 0), 0) / attempts.length;
        
        // Balanced Formula: 40% AI Resume Match, 60% Technical Assessment
        finalScore = Math.round((Number(application.match_score || 0) * 0.4) + (avgAssessmentScore * 0.6));
    }

    // 3. Update the application match score
    await supabase
        .from("job_applications")
        .update({ match_score: finalScore })
        .eq("id", applicationId);

    return finalScore;
}
