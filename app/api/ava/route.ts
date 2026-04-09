import { NextResponse } from 'next/server';

const SYSTEM_PROMPT = `You are Ava, a specialized recruitment AI for HireSight. 
Your goal is to conduct a tactical assessment of candidates. 
Be professional, efficient, and probing. 
Keep your responses concise and naturally conversational.`;

export async function POST(req: Request) {
  try {
    const { messages } = await req.json();

    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
        'HTTP-Referer': 'https://hiresight.vercel.app', // Optional for OpenRouter
        'X-Title': 'HireSight Ava', // Optional for OpenRouter
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'openai/gpt-4o-mini',
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          ...messages
        ],
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || 'Failed to fetch from OpenRouter');
    }

    return NextResponse.json({ 
      text: data.choices[0].message.content 
    });
  } catch (error: any) {
    console.error('[AvaAPI] Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
