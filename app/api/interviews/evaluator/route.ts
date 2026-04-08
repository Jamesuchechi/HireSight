import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { question_id, transcript, sessionId, mode } = body;

    const supabase = await createClient();
    const AI_API_KEY = process.env.MISTRAL_API_KEY;
    const AI_MODEL = process.env.AI_MODEL || 'mistral-large-latest';
    const AI_API_URL = process.env.AI_API_URL || 'https://api.mistral.ai/v1/chat/completions';

    if (!AI_API_KEY) {
        throw new Error("AI_API_KEY is not configured in Vercel/Environment");
    }

    // CASE 1: Session-level Evaluation
    if (sessionId) {
      console.log(`[Evaluator] Running session-level evaluation for ${sessionId}`);
      
      // 1. Fetch all questions and transcripts for the session
      const { data: qData } = await supabase
        .from('practice_questions')
        .select('*')
        .eq('session_id', sessionId);

      if (!qData || qData.length === 0) {
        return NextResponse.json({ message: "No questions to evaluate" });
      }

      // 2. Aggregate transcripts and prompts
      const interviewContext = qData.map(q => `Q: ${q.prompt}\nA: ${q.answer_transcript || 'No answer'}`).join('\n\n');

      const sessionPrompt = `
      You are an elite interview consultant. Evaluate the candidate's performance across the entire session.
      
      INTERVIEW CONTENT:
      ${interviewContext}
      
      RESPONSE FORMAT:
      Return ONLY a JSON object:
      {
        "overall_score": 0-100,
        "strengths": ["..."],
        "improvements": ["..."],
        "cultural_fit": 0-100,
        "technical_depth": 0-100,
        "final_verdict": "Detailed summary..."
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
          messages: [{ role: 'system', content: 'You are a senior hiring bar raiser.' }, { role: 'user', content: sessionPrompt }],
          temperature: 0.3,
          response_format: { type: 'json_object' }
        })
      });

      const aiResult = await response.json();
      const evaluation = JSON.parse(aiResult.choices[0].message.content);

      // 3. Update session
      await supabase
        .from('interview_practice_sessions')
        .update({ 
           evaluation_result: evaluation,
           score: evaluation.overall_score
        })
        .eq('id', sessionId);

      return NextResponse.json(evaluation);
    }

    // CASE 2: Single Question Evaluation
    if (question_id && transcript) {
      const { data: question } = await supabase.from('practice_questions').select('prompt, category, ai_feedback').eq('id', question_id).single();
      if (!question) throw new Error('Question not found');

      const prompt = `
      Evaluate this candidate response.
      QUESTION: ${question.prompt}
      TRANSCRIPT: ${transcript}
      
      Return JSON: { "score": 0-100, "feedback": "...", "technical_score": 0-100 }
      `;

      const response = await fetch(AI_API_URL, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${AI_API_KEY}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: AI_MODEL,
          messages: [{ role: 'system', content: 'You are an interviewer.' }, { role: 'user', content: prompt }],
          temperature: 0.3,
          response_format: { type: 'json_object' }
        })
      });

      const aiResult = await response.json();
      const parsed = JSON.parse(aiResult.choices[0].message.content);

      await supabase
        .from('practice_questions')
        .update({
          answer_transcript: transcript,
          ai_feedback: { ...question.ai_feedback, evaluation: parsed },
          score: parsed.score
        })
        .eq('id', question_id);

      return NextResponse.json(parsed);
    }

    throw new Error('Invalid request parameters');

  } catch (error: any) {
    console.error("[Evaluator API Error]:", error.message);
    return NextResponse.json({ error: error.message }, { status: 400 });
  }
}
