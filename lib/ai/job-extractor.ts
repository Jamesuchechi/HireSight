import { AIOrchestrator } from "./orchestrator";

export async function extractJobDNA(urlOrText: string) {
    try {
        let content = urlOrText;

        // 1. Detect if it's a URL
        const isUrl = /^(https?:\/\/)/.test(urlOrText.trim());

        if (isUrl) {
            // Fetch the content (Server-side)
            const response = await fetch(urlOrText.trim(), {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            });
            content = await response.text();
        }

        // 2. Use our centralized AI Orchestrator
        const prompt = `
            Extract the core Job Description details from this content.
            Focus on: 
            - Role Title
            - Key Responsibilities
            - Required Skills (Hard and Soft)
            - Company Culture/Tone
            - Mission/Goals
            
            STRICT RULES:
            - Return ONLY clean, readable, professional text summary.
            - USE BULLET POINTS for lists.
            - DO NOT return JSON. 
            - DO NOT used curly braces { } or brackets [ ] for structure.
            - DO NOT use technical keys (like "role": "developer").
            - The output must be ready for a human to read and edit.
            
            CONTENT:
            ${content.substring(0, 15000)} // Truncate to fit context window
        `;

        const result = await AIOrchestrator.generate(
            "You are an expert Job DNA Synthesizer.",
            prompt
        );

        return result.content;
    } catch (error) {
        console.error("Job extraction failed:", error);
        throw new Error("Could not extract Job DNA from this URL. Please paste the description manually.");
    }
}
