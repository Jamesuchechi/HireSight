import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { session_id, job_id, candidate_id, difficulty = 'intermediate', focus_areas = [], num_questions = 5 } = await req.json();

    const supabase = await createClient();

    // 1. Fetch Context
    let contextStr = "";

    if (job_id) {
      const { data: job } = await supabase.from('jobs').select('title, description, requirements').eq('id', job_id).single();
      if (job) {
        contextStr += `Job Title: ${job.title}\nDescription: ${job.description}\nRequirements: ${job.requirements}\n\n`;
      }
    }

    if (candidate_id) {
      const { data: profile } = await supabase.from('profiles').select('full_name, headline, bio, skills, experience').eq('id', candidate_id).single();
      if (profile) {
        contextStr += `Candidate: ${profile.full_name}\nHeadline: ${profile.headline}\nBio: ${profile.bio}\nSkills: ${JSON.stringify(profile.skills)}\nExperience: ${JSON.stringify(profile.experience)}\n\n`;
      }
    }

    // 2. Call AI (Mistral/Gemini/OpenAI compatible)
    const AI_API_KEY = process.env.MISTRAL_API_KEY;
    const AI_MODEL = process.env.AI_MODEL || 'mistral-large-latest';
    const AI_API_URL = process.env.AI_API_URL || 'https://api.mistral.ai/v1/chat/completions';

    if (!AI_API_KEY) {
        throw new Error("AI_API_KEY is not configured in Vercel/Environment");
    }

    const prompt = `
    You are an expert interview question generator for HireSight, an AI-powered recruitment platform.
    Generate exactly ${num_questions} high-quality, realistic interview questions for a ${difficulty} level interview.
    
    FOCUS AREAS: ${focus_areas.join(', ') || 'General Mix'}
    
    CONTEXT:
    ${contextStr}
    
    RESPONSE FORMAT:
    Return ONLY a JSON object (no markdown, no extra text) with this exact structure:
    {
      "questions": [
        {
          "prompt": "The interview question as a string",
          "category": "behavioral|technical|situational",
          "difficulty": "easy|medium|hard",
          "evaluation_criteria": ["criterion1", "criterion2"],
          "expected_answer_elements": ["element1", "element2"]
        }
      ]
    }
    `;

    const response = await fetch(AI_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: AI_MODEL,
        messages: [
          { role: 'system', content: 'You are an elite technical and behavioral interviewer.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.7,
        response_format: { type: 'json_object' }
      })
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`AI API Error: ${response.status} - ${errorText}`);
    }

    const aiResult = await response.json();
    const content = aiResult.choices[0].message.content;
    const parsed = JSON.parse(content);

    // 3. Store if session_id is provided
    if (session_id && parsed.questions) {
      const questionsToInsert = parsed.questions.map((q: any, index: number) => ({
        session_id,
        prompt: q.prompt,
        category: q.category,
        order_index: index,
        ai_feedback: { evaluation_criteria: q.evaluation_criteria, expected_elements: q.expected_answer_elements }
      }));

      const { error: insertError } = await supabase.from('practice_questions').insert(questionsToInsert);
      if (insertError) throw insertError;

      // Update session status
      await supabase.from('interview_practice_sessions').update({ status: 'in_progress' }).eq('id', session_id);
    }

    return NextResponse.json(parsed);

  } catch (error: any) {
    console.error("[Generator API Error]:", error.message);
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
}
