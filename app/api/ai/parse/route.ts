import { NextRequest, NextResponse } from "next/server";
import { ResumeParser } from "@/lib/ai/resume-parser";
// @ts-ignore
import pdf from "pdf-parse/lib/pdf-parse.js";

export async function POST(req: NextRequest) {
    try {
        const formData = await req.formData();
        const file = formData.get("file") as File;

        if (!file) {
            return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
        }

        let resumeText = "";

        if (file.type === "application/pdf") {
            const buffer = Buffer.from(await file.arrayBuffer());
            const data = await pdf(buffer);
            resumeText = data.text;
        } else {
            // Assume plain text for other types like .txt
            resumeText = await file.text();
        }

        if (!resumeText || resumeText.trim().length < 50) {
            return NextResponse.json({ error: "Resume content is too short or unreadable." }, { status: 400 });
        }

        // Trigger the Resilient AI Parser
        const structuredData = await ResumeParser.parse(resumeText);

        return NextResponse.json(structuredData);
    } catch (error: any) {
        console.error("[API Parse Error]:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
