import { AccessToken } from "livekit-server-sdk";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const room = searchParams.get("room");
    const username = searchParams.get("username") || "AgentCandidate";

    if (!room) {
        return NextResponse.json({ error: 'Missing room parameter' }, { status: 400 });
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const wsUrl = process.env.NEXT_PUBLIC_LIVEKIT_URL;

    if (!apiKey || !apiSecret || !wsUrl) {
        return NextResponse.json({ error: 'Server misconfigured' }, { status: 500 });
    }

    const at = new AccessToken(apiKey, apiSecret, {
        identity: username,
    });

    at.addGrant({ 
        roomJoin: true, 
        room: room,
        canPublish: true,
        canSubscribe: true,
        canPublishData: true
    });

    return NextResponse.json({ 
        token: await at.toJwt(),
        url: wsUrl 
    });
}
