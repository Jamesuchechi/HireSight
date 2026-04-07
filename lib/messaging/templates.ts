// Smart Variable Injection for Messaging Templates

interface TemplateContext {
    candidate_name?: string;
    job_title?: string;
    company_name?: string;
    interview_date?: string;
}

/**
 * Injects contextual variables into a message template string.
 * Example: "Hi {candidate_name}, welcome to {company_name}!" 
 * -> "Hi John, welcome to HireSight!"
 */
export const injectVariables = (template: string, context: TemplateContext): string => {
    let result = template;

    if (context.candidate_name) {
        result = result.replace(/{candidate_name}/g, context.candidate_name);
    }
    if (context.job_title) {
        result = result.replace(/{job_title}/g, context.job_title);
    }
    if (context.company_name) {
        result = result.replace(/{company_name}/g, context.company_name);
    }
    if (context.interview_date) {
        result = result.replace(/{interview_date}/g, context.interview_date);
    }

    return result;
};

/**
 * Common Smart Templates for Recruiters
 */
export const SEED_TEMPLATES = [
    {
        name: "Initial Outreach",
        category: "general",
        subject: "Neural Sync Request: {job_title}",
        content: "Hi {candidate_name}, I'm impressed by your background. We are currently scouting for a {job_title} at {company_name} and your profile shows high alignment with our neural criteria. Would you be open to a quick sync?"
    },
    {
        name: "Interview Invitation",
        category: "interview",
        subject: "Mission Briefing: Interview for {job_title}",
        content: "Hello {candidate_name}! Your screening phase was successful. We'd like to invite you for a neural synchronization (interview) for the {job_title} position. Let us know your availability for {interview_date}."
    },
    {
        name: "Offer Extended",
        category: "offer",
        subject: "Protocol Finalized: Offer for {job_title}",
        content: "Congratulations {candidate_name}! We are thrilled to extend an official offer for the {job_title} role at {company_name}. You have demonstrated unmatched skill density during our vetted cycles."
    }
];
