const {
  cli,
  voice,
  defineAgent,
  WorkerOptions,
} = require('@livekit/agents');
const openai = require('@livekit/agents-plugin-openai');
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables from .env or .env.local
dotenv.config();

// Ensure LiveKit credentials are set for the agent worker
if (process.env.NEXT_PUBLIC_LIVEKIT_URL && !process.env.LIVEKIT_URL) {
  process.env.LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL;
}

const SYSTEM_PROMPT = `You are Ava, a specialized recruitment AI for HireSight. 
Your goal is to conduct a tactical assessment of candidates. 
Be professional, efficient, and probing.`;

const agent = defineAgent({
  entry: async (ctx: import('@livekit/agents').JobContext) => {
    console.log(`Connecting to room ${ctx.room.name}`);

    await ctx.connect();

    const participant = await ctx.waitForParticipant();
    console.log(`Starting voice protocol for participant ${participant.identity}`);

    const model = new openai.realtime.RealtimeModel({
      modalities: ['audio', 'text'],
    });

    const agentInstance = new voice.Agent({
      instructions: SYSTEM_PROMPT,
      llm: model,
    });

    const session = new voice.AgentSession({
      llm: model,
    });

    await session.start({
      agent: agentInstance,
      room: ctx.room,
    });

    await session.say(
      "Initializing Screening Protocol. I am Ava. Let's begin the tactical assessment."
    );

    ctx.room.on('disconnected', () => {
      console.log('Room disconnected, agent exiting.');
    });
  },
});

// LiveKit worker expects the agent as the default export
module.exports.default = agent;

if (require.main === module) {
  cli.runApp(
    new WorkerOptions({
      agent: __filename,
    })
  );
}