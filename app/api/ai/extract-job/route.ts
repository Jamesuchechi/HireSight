import { NextRequest, NextResponse } from "next/server";
import { extractJobDNA } from "@/lib/ai/job-extractor";

export async function POST(req: NextRequest) {
    try {
        const { url } = await req.json();

        if (!url) {
            return NextResponse.json({ error: "Job URL is required" }, { status: 400 });
        }

        const extracted = await extractJobDNA(url);

        return NextResponse.json({ extracted });
    } catch (error: any) {
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
