import { AIModel, modelRegistry } from "./models";

export interface AIResponse {
    content: string;
    model: string;
    provider: string;
}

export class AIOrchestrator {
    private static async callProvider(model: AIModel, messages: any[]): Promise<string> {
        const apiKey = {
            groq: process.env.GROQ_API_KEY,
            mistral: process.env.MISTRAL_API_KEY,
            openrouter: process.env.OPENROUTER_API_KEY,
        }[model.provider];

        if (!apiKey) throw new Error(`Missing API key for ${model.provider}`);

        const url = {
            groq: "https://api.groq.com/openai/v1/chat/completions",
            mistral: "https://api.mistral.ai/v1/chat/completions",
            openrouter: "https://openrouter.ai/api/v1/chat/completions",
        }[model.provider];

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${apiKey}`,
                ...(model.provider === "openrouter" ? { "HTTP-Referer": "https://hiresight.ai", "X-Title": "HireSight" } : {}),
            },
            body: JSON.stringify({
                model: model.id,
                messages,
                temperature: 0.1, // Low temperature for stability in structured output
                max_tokens: 4000,
                response_format: { type: "json_object" } // Force JSON for modern providers
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || `HTTP ${response.status} from ${model.provider}`);
        }

        const data = await response.json();
        return data.choices[0].message.content;
    }

    /**
     * Executes AI generation with iterative fallback across 12 models.
     */
    static async generate(system: string, user: string): Promise<AIResponse> {
        const messages = [
            { role: "system", content: system },
            { role: "user", content: user }
        ];

        let lastError: Error | null = null;

        // Iterate through the entire registry until success
        for (const model of modelRegistry) {
            try {
                console.log(`[AI] Attempting ${model.name} (${model.provider})...`);
                const content = await this.callProvider(model, messages);
                
                return {
                    content,
                    model: model.id,
                    provider: model.provider
                };
            } catch (error: any) {
                console.warn(`[AI] ${model.name} failed: ${error.message}`);
                lastError = error;
                // Move to next model in the registry
                continue;
            }
        }

        throw new Error(`All AI providers exhausted. Last error: ${lastError?.message}`);
    }
}
