import { NextRequest, NextResponse } from "next/server";
import { ResumeParser } from "@/lib/ai/resume-parser";
import { PDFParse } from "pdf-parse";
import { getData } from "pdf-parse/worker";

// Force initialize the worker for Next.js/Turbopack environments
PDFParse.setWorker(getData());
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
            const parser = new PDFParse({ data: buffer });
            const result = await parser.getText();
            resumeText = result.text;
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
