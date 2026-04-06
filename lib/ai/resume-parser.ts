import { AIOrchestrator } from "./orchestrator";

export interface ParsedResume {
    fullName: string;
    contact: {
        email: string;
        phone: string;
        location: string;
        links: string[];
    };
    summary: string;
    skills: {
        hard: string[];
        soft: string[];
        tools: string[];
    };
    experience: {
        company: string;
        role: string;
        duration: string;
        highlights: string[];
    }[];
    education: {
        institution: string;
        degree: string;
        year: string;
    }[];
}

export class ResumeParser {
    private static systemPrompt = `
        You are an expert recruitment AI specialized in data extraction. 
        Extract a structured JSON profile from the provided resume text. 
        Maintain zero hallucination—only extract what is present. 
        Ensure you return exactly one JSON object following the schema provided.
        
        REQUIRED JSON SCHEMA:
        {
            "fullName": string,
            "contact": { "email": string, "phone": string, "location": string, "links": string[] },
            "summary": string,
            "skills": { "hard": string[], "soft": string[], "tools": string[] },
            "experience": [{ "company": string, "role": string, "duration": string, "highlights": string[] }],
            "education": [{ "institution": string, "degree": string, "year": string }]
        }
    `;

    static async parse(resumeText: string): Promise<ParsedResume> {
        try {
            console.log("[AI] Starting Resume Parsing...");
            const response = await AIOrchestrator.generate(
                this.systemPrompt,
                `Resume Content:\n\n${resumeText}`
            );

            const parsedData = JSON.parse(response.content);
            return parsedData as ParsedResume;
        } catch (error: any) {
            console.error(`[AI Parser] Failed: ${error.message}`);
            throw new Error(`Failed to parse resume with AI: ${error.message}`);
        }
    }
}
