const {
  cli,
  voice,
  defineAgent,
  WorkerOptions,
} = require('@livekit/agents');
const openai = require('@livekit/agents-plugin-openai');
const deepgram = require('@livekit/agents-plugin-deepgram');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config();

// Ensure LiveKit credentials are set
if (process.env.NEXT_PUBLIC_LIVEKIT_URL && !process.env.LIVEKIT_URL) {
  process.env.LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL;
}

const SYSTEM_PROMPT = `You are Ava, a specialized recruitment AI for HireSight. 
Your goal is to conduct a tactical assessment of candidates. 
Be professional, efficient, and probing. 
Keep your responses concise and naturally conversational.`;

const agent = defineAgent({
  entry: async (ctx: import('@livekit/agents').JobContext) => {
    console.log(`[AvaAgent] Initializing mission protocols for room: ${ctx.room.name}`);

    await ctx.connect();

    const participant = await ctx.waitForParticipant();
    console.log(`[AvaAgent] Target participant identified: ${participant.identity}`);

    // Standardized Voice Pipeline (Vercel-Compatible Architecture)
    const assistant = new voice.VoiceAssistant({
      stt: new deepgram.STT(), // Requires DEEPGRAM_API_KEY in .env
      llm: new openai.LLM({
          model: 'openai/gpt-4o-mini', // High speed, low latency model via OpenRouter
          apiKey: process.env.OPENROUTER_API_KEY,
          baseURL: 'https://openrouter.ai/api/v1',
      }),
      tts: new deepgram.TTS(), // Requires DEEPGRAM_API_KEY in .env
    });

    console.log("[AvaAgent] Neural Hub online. Starting Voice Protocol...");

    assistant.start(ctx.room, participant);

    await assistant.say(
      "Initializing Screening Protocol. I am Ava. It is a pleasure to meet you. Let's begin the tactical assessment."
    );

    ctx.room.on('disconnected', () => {
      console.log('[AvaAgent] Mission terminated, room disconnected.');
    });
  },
});

module.exports.default = agent;

if (require.main === module) {
  cli.runApp(
    new WorkerOptions({
      agent: __filename,
    })
  );
}