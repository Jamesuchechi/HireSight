import { NextRequest, NextResponse } from "next/server";
import { AIMatcher } from "@/lib/ai/matcher";

export async function POST(req: NextRequest) {
    try {
        const { candidateProfile, jobDescription } = await req.json();

        if (!candidateProfile || !jobDescription) {
            return NextResponse.json({ error: "Missing profile or job description" }, { status: 400 });
        }

        // Trigger the Resilient AI Matcher
        const matchResult = await AIMatcher.match(candidateProfile, jobDescription);

        return NextResponse.json(matchResult);
    } catch (error: any) {
        console.error("[API Match Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
