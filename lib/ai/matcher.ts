import { AIOrchestrator } from "./orchestrator";

export interface MatchResult {
    score: number;
    summary: string;
    pros: string[];
    cons: string[];
    skillGaps: string[];
    nextSteps: string;
}

export class AIMatcher {
    private static systemPrompt = `
        You are an expert AI Recruiting Strategist. 
        Compare the provided Candidate Profile with the Job Description. 
        Calculate a compatibility score (0-100), a concise professional summary, list top pros/cons, identify skill gaps, and recommend next steps.
        
        REQUIRED JSON SCHEMA:
        {
            "score": number,
            "summary": string,
            "pros": string[],
            "cons": string[],
            "skillGaps": string[],
            "nextSteps": string
        }
    `;

    static async match(candidateProfile: any, jobDescription: any): Promise<MatchResult> {
        try {
            console.log("[AI] Starting Matching Analysis...");
            const response = await AIOrchestrator.generate(
                this.systemPrompt,
                `Candidate Profile: ${JSON.stringify(candidateProfile)}\n\nJob Description: ${JSON.stringify(jobDescription)}`
            );

            const resultData = JSON.parse(response.content);
            return resultData as MatchResult;
        } catch (error: any) {
            console.error(`[AI Matcher] Failed: ${error.message}`);
            throw new Error(`Failed to calculate AI match: ${error.message}`);
        }
    }
}
