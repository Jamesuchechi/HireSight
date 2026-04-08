const agents = require('@livekit/agents');

const run = async (ctx: import('@livekit/agents').JobContext) => {
  console.log('Successfully used inline import type');
}

run({} as any);
