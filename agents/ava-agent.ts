import {
  type JobContext,
  Worker,
  AutoSubscribe,
  cli,
  multimodal,
} from '@livekit/agents';
import * as openai from '@livekit/agents-plugin-openai';
import * as dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(process.cwd(), '.env.local') });

// ============================================================
// HiréSight Tactical Protocol: Ava System Prompt
// ============================================================
const SYSTEM_PROMPT = `
You are Ava, the Autonomous Voice Assistant for HiréSight. 
Your mission is to conduct a professional tactical screening mission for a high-stakes job application.

PRONOUNCE Your Name: Aye-vah.

OPERATIONAL PARAMETERS:
1. BE PROFESSIONAL & TACTICAL: Use a tone that is efficient, empathetic but mission-driven. 
2. STAR FRAMEWORK: Focus on Situation, Task, Action, and Result. If a candidate is vague, probe deeper.
3. ADAPTIVE LOGIC: Ask follow-up questions based on their specific answers. Don't just read a list.
4. NO SMALL TALK: Be polite but get straight to the assessment.
5. DEBRIEF: At the end of the session, briefly thank them and inform them the mission data is being processed.

MANDATORY PHRASES:
- "Initializing Screening Protocol..."
- "Engaging STAR analysis for that scenario..."
- "Tactical window concluding. Mission results will be dispatched to your dashboard."
`;

async function entrypoint(ctx: JobContext) {
  console.log(`Connecting to room ${ctx.room.name}`);

  await ctx.connect({ autoSubscribe: AutoSubscribe.AUDIO_ONLY });

  // Wait for the first participant to join
  const participant = await ctx.waitForParticipant();
  console.log(`Starting voice protocol for participant ${participant.identity}`);

  // Initialize OpenAI Realtime Model
  const model = new openai.realtime.RealtimeModel({
    instructions: SYSTEM_PROMPT,
    modalities: ['audio', 'text'],
  });

  const agent = new multimodal.MultimodalAgent({ model });
  agent.start(ctx.room, participant);

  // Greet the candidate
  await agent.say("Initializing Screening Protocol. I am Ava. Let's begin the tactical assessment.");

  // Clean up on disconnect
  ctx.room.on('disconnected', () => {
    console.log('Room disconnected, agent exiting.');
  });
}

// Run the agent worker
cli.runApp(new Worker({ entrypoint }));
