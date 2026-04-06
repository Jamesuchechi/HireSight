export type AIProvider = "groq" | "mistral" | "openrouter";

export interface AIModel {
    id: string;
    provider: AIProvider;
    name: string;
    description: string;
}

export const modelRegistry: AIModel[] = [
    // --- GROQ (Speed + High Throughput) ---
    { 
        id: "llama-3.3-70b-versatile", 
        provider: "groq", 
        name: "Llama 3.3 70B", 
        description: "Primary choice for complex reasoning & speed." 
    },
    { 
        id: "mixtral-8x7b-32768", 
        provider: "groq", 
        name: "Mixtral 8x7B", 
        description: "Stable fallback for large context windows." 
    },
    { 
        id: "gemma2-9b-it", 
        provider: "groq", 
        name: "Gemma 2 9B", 
        description: "Highly efficient for shorter extractions." 
    },
    { 
        id: "llama-3.1-8b-instant", 
        provider: "groq", 
        name: "Llama 3.1 8B", 
        description: "Ultra-low latency for simple parsing." 
    },

    // --- MISTRAL (High Quality + Specialized) ---
    { 
        id: "mistral-large-latest", 
        provider: "mistral", 
        name: "Mistral Large", 
        description: "Premium model for complex architectural matching." 
    },
    { 
        id: "mistral-small-latest", 
        provider: "mistral", 
        name: "Mistral Small", 
        description: "Cost-effective, high-accuracy processing." 
    },
    { 
        id: "open-mixtral-8x22b", 
        provider: "mistral", 
        name: "Mixtral 8x22B", 
        description: "Large context window for long resumes." 
    },
    { 
        id: "pixtral-12b", 
        provider: "mistral", 
        name: "Pixtral 12B", 
        description: "Balanced performance for structured output." 
    },

    // --- OPENROUTER (Final Redundancy) ---
    { 
        id: "meta-llama/llama-3.1-70b-instruct", 
        provider: "openrouter", 
        name: "Llama 3.1 70B (OR)", 
        description: "Standard instruct model via OpenRouter." 
    },
    { 
        id: "google/gemma-2-9b-it", 
        provider: "openrouter", 
        name: "Gemma 2 9B (OR)", 
        description: "Google's ultra-balanced instruction model." 
    },
    { 
        id: "mistralai/mistral-7b-instruct:free", 
        provider: "openrouter", 
        name: "Mistral 7B (Free)", 
        description: "No-cost redundancy layer." 
    },
    { 
        id: "microsoft/phi-3-medium-128k-instruct:free", 
        provider: "openrouter", 
        name: "Phi-3 Medium (Free)", 
        description: "High-efficiency specialized instruct model." 
    }
];
