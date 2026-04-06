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

        const { section, content, jobDescription, metricsFocus, fullEvolution, template } = await req.json();

        // Persona Mapping based on Template
        const personas: Record<string, string> = {
            executive: "You are a high-level Executive Search consultant. Focus on ROI, strategic leadership, and P&L impact. Use powerful action verbs.",
            creative: "You are a Creative Director. Use a punchy, narrative-driven tone. Focus on storytelling, unique value, and personal brand voice.",
            technical: "You are a Senior Engineering Manager. Focus on tech stack proficiency, architecture, and specific technical achievements. Keyword-optimized for ATS and technical reviewers.",
            modern: "You are a Modern Career Coach. Focus on high-impact results and sleek professional branding.",
            classic: "You are a Traditional Corporate Recruiter. Focus on deep industry expertise and structured, dense professional history.",
            minimal: "You are a Minimalist Design Strategist. Focus on precision, brevity, and high-signal content."
        };

        const chosenPersona = personas[template as string] || personas.modern;

        // 1. Fetch Resume Data (to ensure ownership)
        const { data: resume, error } = await supabase
            .from("resumes")
            .select("user_id, parsed_content")
            .eq("id", id)
            .eq("user_id", user.id)
            .single();

        if (error || !resume) throw new Error("Resume not found");

        // 2. AI Tailoring Logic (High-Fidelity Synthesis)
        const systemPrompt = `
            ${chosenPersona}
            
            Tailor the provided resume content to move perfectly in sync with the job description.
            
            SCOPE: ${fullEvolution ? 'WHOLE RESUME EVOLUTION' : `SINGLE SECTION: ${section}`}
            
            STRICT RULES:
            1. Return ONLY the human-readable rewritten text.
            2. NEVER return JSON, curly braces, or technical keys (like "skills": { "hard": ... }).
            3. Use professional Markdown: bullets, bold headers, and clean spacing.
            4. If fullEvolution is true, rewrite EVERYTHING (Summary, Skills, Experience) into a professional, cohesive narrative.
            5. Focus on ${metricsFocus || 'quantifiable impact and industry keywords'}.
            6. Thinking like a high-end copywriter. No technical jargon wrappers.
        `;

        const userPrompt = `
            Target Job Description: ${jobDescription}
            Existing Content: ${fullEvolution ? JSON.stringify(resume.parsed_content) : content}
        `;

        const aiResponse = await AIOrchestrator.generate(systemPrompt, userPrompt);

        return NextResponse.json({ 
            original: content,
            rewritten: aiResponse.content,
            section,
            fullEvolution
        });
    } catch (error: any) {
        console.error("Rewrite failed:", error);
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
}
