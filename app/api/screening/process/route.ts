import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { ScreeningEngine } from "@/lib/ai/screening-engine";
import { notifyServer } from "@/lib/notifications/notify-server";


export async function POST(req: NextRequest) {
    try {
        const supabase = await createClient();
        const { sessionId, resumeUrl } = await req.json();

        if (!sessionId || !resumeUrl) {
            return NextResponse.json({ error: "Missing sessionId or resumeUrl" }, { status: 400 });
        }

        // 1. Fetch Session and Criteria
        const { data: session, error: sessionError } = await supabase
            .from("screening_sessions")
            .select("*")
            .eq("id", sessionId)
            .single();

        if (sessionError || !session) throw new Error("Session not found");

        // 2. Fetch and Parse PDF
        console.log(`[Screening Worker] Processing: ${resumeUrl}`);
        const response = await fetch(resumeUrl);
        const buffer = Buffer.from(await response.arrayBuffer());
        
        const { PDFParse } = await import("pdf-parse");
        const parser = new PDFParse({ data: buffer });
        const pdfData = await parser.getText();
        const resumeText = pdfData.text;

        // 3. Screen Resume
        const result = await ScreeningEngine.screen(resumeText, {
            ...session.criteria,
            weights: {
                skills: session.criteria.weights.skills,
                experience: session.criteria.weights.experience,
                education: session.criteria.weights.education,
                keywords: session.criteria.weights.keywords,
                questions: session.weight_screening_questions || 0,
                assessments: session.weight_assessments || 0
            }
        });

        // 4. Save Result
        const { data: resultRecord, error: resultError } = await supabase
            .from("screening_results")
            .insert({
                session_id: sessionId,
                candidate_name: result.candidate.fullName,
                candidate_email: result.candidate.contact.email,
                resume_url: resumeUrl,
                match_score: result.match_score,
                analysis: {
                    skills_score: result.skills_score,
                    exp_score: result.exp_score,
                    edu_score: result.edu_score,
                    keyword_score: result.keyword_score,
                    question_score: result.question_score,
                    assessment_score: result.assessment_score,
                    keyword_matches: result.keyword_matches,
                    gaps: result.missing_skills,
                    summary: result.summary,
                    explanation: result.explanation
                },
                status: 'completed'
            })
            .select()
            .single();

        if (resultError) throw resultError;

        // 5. Update Session Progress
        await supabase.rpc('increment_processed_count', { session_row_id: sessionId });

        // 6. Notify session creator (recruiter) that screening is done
        await notifyServer(session.created_by, {
            title: "Neural Screening Complete",
            message: `A candidate scored ${result.match_score}% on your screening session.`,
            type: "screening_completed",
            action_url: `/dashboard/screening`,
            action_text: "View Results"
        });

        return NextResponse.json(resultRecord);
    } catch (error: any) {
        console.error("[API Screening Process Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
