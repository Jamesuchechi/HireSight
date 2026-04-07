import { createClient } from "@/lib/supabase/server";
import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    try {
        const supabase = await createClient();
        const { data: { user } } = await supabase.auth.getUser();

        if (!user) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { title, jobId, totalFiles, criteria, weightQuestions, weightAssessments, questionsConfig } = await req.json();

        if (!title || !totalFiles) {
            return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
        }

        const { data, error } = await supabase
            .from("screening_sessions")
            .insert({
                company_id: user.id,
                job_id: jobId || null,
                title,
                total_files: totalFiles,
                criteria: criteria || {},
                weight_screening_questions: weightQuestions || 0,
                weight_assessments: weightAssessments || 0,
                screening_questions_config: questionsConfig || {},
                status: 'pending'
            })
            .select()
            .single();

        if (error) throw error;

        return NextResponse.json(data);
    } catch (error: any) {
        console.error("[API Screening Create Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
