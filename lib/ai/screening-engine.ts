import { AIOrchestrator } from "./orchestrator";
import { ResumeParser, ParsedResume } from "./resume-parser";

export interface ScreeningCriteria {
    requiredSkills: string[];
    niceToHaveSkills: string[];
    minExperience: number;
    educationLevel: string;
    keywords: string[];
    weights: {
        skills: number;
        experience: number;
        education: number;
        keywords: number;
        questions: number;
        assessments: number;
    };
    screeningQuestions?: any[];
    assessmentResults?: any[];
}

export interface ScreeningAnalysis {
    match_score: number;
    skills_score: number;
    exp_score: number;
    edu_score: number;
    keyword_score: number;
    question_score: number;
    assessment_score: number;
    matched_skills: string[];
    missing_skills: string[];
    keyword_matches: string[];
    summary: string;
    explanation: string;
}

export class ScreeningEngine {
    private static systemPrompt = `
        You are an expert recruitment AI specialized in batch resume screening. 
        Compare the provided Candidate Profile against the Screening Criteria. 
        Calculate granular scores for Skills, Experience, Education, and Keywords.
        
        WEIGHTS TO USE IN FINAL CALCULATION:
        - Skills: {skills_weight}%
        - Experience: {exp_weight}%
        - Education: {edu_weight}%
        - Keywords: {keywords_weight}%
        - Screening Questions: {questions_weight}%
        - Assessments: {assessments_weight}%
        
        REQUIRED JSON SCHEMA:
        {
            "match_score": number (0-100),
            "skills_score": number (0-100),
            "exp_score": number (0-100),
            "edu_score": number (0-100),
            "keyword_score": number (0-100),
            "question_score": number (0-100),
            "assessment_score": number (0-100),
            "matched_skills": string[],
            "missing_skills": string[],
            "keyword_matches": string[],
            "summary": string,
            "explanation": string
        }
    `;

    static async screen(resumeText: string, criteria: ScreeningCriteria): Promise<ScreeningAnalysis & { candidate: ParsedResume }> {
        try {
            console.log("[AI] Parsing Resume for Screening...");
            const candidate = await ResumeParser.parse(resumeText);

            console.log("[AI] Executing Weighted Screening Analysis...");
            
            // Customize prompt with dynamic weights
            const customizedPrompt = this.systemPrompt
                .replace("{skills_weight}", criteria.weights.skills.toString())
                .replace("{exp_weight}", criteria.weights.experience.toString())
                .replace("{edu_weight}", criteria.weights.education.toString())
                .replace("{keywords_weight}", criteria.weights.keywords.toString())
                .replace("{questions_weight}", (criteria.weights.questions || 0).toString())
                .replace("{assessments_weight}", (criteria.weights.assessments || 0).toString());

            const response = await AIOrchestrator.generate(
                customizedPrompt,
                `Candidate Profile: ${JSON.stringify(candidate)}\n\nScreening Criteria: ${JSON.stringify(criteria)}\n\nSub-Metrics (Context Only): ${JSON.stringify({ questions: criteria.screeningQuestions, assessments: criteria.assessmentResults })}`
            );

            const analysis = JSON.parse(response.content);
            return {
                ...analysis,
                candidate
            };
        } catch (error: any) {
            console.error(`[Screening Engine] Failed: ${error.message}`);
            throw new Error(`Failed to screen resume: ${error.message}`);
        }
    }
}
