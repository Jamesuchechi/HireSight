import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { AIOrchestrator } from "@/lib/ai/orchestrator";

export async function POST(
    req: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        const { id } = await params;
        const supabase = await createClient();
        const { data: { user } } = await supabase.auth.getUser();

        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { jobDescription } = await req.json();

        // 1. Fetch Resume Data
        const { data: resume, error } = await supabase
            .from("resumes")
            .select("*")
            .eq("id", id)
            .eq("user_id", user.id)
            .single();

        if (error || !resume) throw new Error("Resume not found");

        const resumeText = JSON.stringify(resume.parsed_content);

        // 2. AI Optimization & ATS Scoring
        const systemPrompt = `
            You are an expert ATS (Applicant Tracking System) optimizer and recruitment consultant.
            Analyze the provided resume against the job description.
            Calculate three key scores (0-100):
            1. ATS Profile Score: How well keywords and format match ATS expectations.
            2. Impact Score: How well the experience highlights quantify achievements.
            3. Action Verb Score: Evaluation of professional, strong action verbs.
            
            Also provide 3-5 specific, tactical suggestions for improvement.
            Return EXACTLY a JSON object with this schema:
            {
                "score": number,
                "metrics": { "impact": number, "verbs": number, "keywords": number },
                "suggestions": [{ "category": string, "title": string, "description": string }]
            }
        `;

        const userPrompt = `
            Job Description: ${jobDescription || "Standard industry benchmarks"}
            Resume DNA: ${resumeText}
        `;

        const aiResponse = await AIOrchestrator.generate(systemPrompt, userPrompt);
        const optimizationResults = JSON.parse(aiResponse.content);

        return NextResponse.json(optimizationResults);
    } catch (error: any) {
        console.error("Optimization failed:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
