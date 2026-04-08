import { serve } from "std/http/server.ts"
import { createClient } from "@supabase/supabase-js"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
}

serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { question_id, transcript, video_metrics = null, criteria = [] } = await req.json()

    if (!question_id || !transcript) {
      throw new Error('Missing question_id or transcript')
    }

    const supabase = createClient(
      Deno.env.get('NEXT_PUBLIC_SUPABASE_URL') ?? '',
      Deno.env.get('NEXT_PUBLIC_SUPABASE_ANON_KEY') ?? ''
    )

    // 1. Fetch Question Context
    const { data: question } = await supabase.from('practice_questions').select('prompt, category, ai_feedback').eq('id', question_id).single()
    if (!question) throw new Error('Question not found')

    // 2. Call AI for Evaluation (STAR framework focused)
    const AI_API_KEY = Deno.env.get('AI_API_KEY')
    const AI_MODEL = Deno.env.get('AI_MODEL') || 'mistral-large-latest'
    const AI_API_URL = Deno.env.get('AI_API_URL') || 'https://api.mistral.ai/v1/chat/completions'

    const prompt = `
    You are an expert interviewer for HireSight. Evaluate the following candidate response to the interview question below.
    
    QUESTION PROMPT: ${question.prompt}
    CATEGORY: ${question.category}
    TRANSCRIPT: ${transcript}
    
    EVALUATION RUBRIC:
    - Use the STAR framework (Situation, Task, Action, Result) for behavioral questions.
    - Rate technical accuracy and depth for technical questions.
    - Consider clarity, confidence, and professionalism.
    
    RESPONSE FORMAT:
    Return ONLY a JSON object with this exact structure:
    {
      "score": 0-100,
      "star_breakdown": {
        "situation": "Analysis...",
        "task": "Analysis...",
        "action": "Analysis...",
        "result": "Analysis..."
      },
      "strengths": ["..."],
      "improvements": ["..."],
      "technical_score": 0-100,
      "overall_feedback": "Detailed feedback..."
    }
    `

    const response = await fetch(AI_API_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${AI_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: AI_MODEL,
        messages: [
          { role: 'system', content: 'You are a neutral, high-performance interview evaluator.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.3,
        response_format: { type: 'json_object' }
      })
    })

    const aiResult = await response.json()
    const content = aiResult.choices[0].message.content
    const parsed = JSON.parse(content)

    // 3. Update practice_questions with evaluation result
    const { error: updateError } = await supabase
      .from('practice_questions')
      .update({
        answer_transcript: transcript,
        ai_feedback: { ...question.ai_feedback, evaluation: parsed },
        score: parsed.score
      })
      .eq('id', question_id)

    if (updateError) throw updateError

    return new Response(JSON.stringify(parsed), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    return new Response(JSON.stringify({ error: errorMessage }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})
