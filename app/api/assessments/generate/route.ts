import { NextRequest, NextResponse } from "next/server";
import { AIOrchestrator } from "@/lib/ai/orchestrator";

export async function POST(req: NextRequest) {
    try {
        const { jobTitle, jobDescription, skill, count = 5 } = await req.json();

        if (!skill && (!jobTitle || !jobDescription)) {
            return NextResponse.json({ error: "Mission parameters incomplete (Provide a Skill or a Job Description)" }, { status: 400 });
        }

        const target = skill || `${jobTitle} (${jobDescription.substring(0, 100)}...)`;

        const systemPrompt = `You are a Senior Technical Recruiter and Assessment Architect. 
Your goal is to generate high-quality, challenging technical assessment questions for a specific job role.
Format the response as a strict JSON object with a 'questions' array.
Each question must have:
- 'text': The inquiry.
- 'type': 'mcq'.
- 'options': An array of 4 distinct strings.
- 'correctAnswer': The 0-based index of the correct option.
- 'explanation': A deep technical explanation (2-3 sentences) on why that specific answer is correct and why the others are not.
- 'points': Integer (1-5 based on difficulty).

Output ONLY the JSON object.`;

        const userPrompt = `Generate ${count} technical MCQ questions for the following target:
Target: ${target}

Ensure questions cover core fundamentals, best practices, and advanced architectural concepts related to this skill/role.`;

        const aiResponse = await AIOrchestrator.generate(systemPrompt, userPrompt);
        const data = JSON.parse(aiResponse.content);

        return NextResponse.json(data);

    } catch (error: any) {
        console.error("[Assessment Gen Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
