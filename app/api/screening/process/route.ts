import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";
import { ScreeningEngine } from "@/lib/ai/screening-engine";


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
        
        // @ts-ignore - pdf-parse lacks type declarations at this path
        const { default: pdf } = await import("pdf-parse/lib/pdf-parse.js");
        const pdfData = await pdf(buffer);
        const resumeText = pdfData.text;

        // 3. Screen Resume
        const result = await ScreeningEngine.screen(resumeText, session.criteria);

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

        return NextResponse.json(resultRecord);
    } catch (error: any) {
        console.error("[API Screening Process Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
