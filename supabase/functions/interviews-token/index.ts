import { createClient } from "@supabase/supabase-js";
import { AccessToken } from "livekit-server-sdk";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req) => {
  // 1. Handle CORS Preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization") || req.headers.get("authorization");
    
    if (!authHeader) {
      console.error("[AUTH] Missing Authorization header");
      return new Response(JSON.stringify({ 
        error: "Missing Authorization header",
        details: "No Bearer token found in request headers." 
      }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const token = authHeader.replace("Bearer ", "").trim();
    
    // Diagnostic Trace
    console.log(`[AUTH] Token Length: ${token.length}`);
    console.log(`[AUTH] Token Prefix: ${token.substring(0, 10)}...`);

    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      {
        global: {
          headers: { Authorization: authHeader },
        },
      }
    );
    
    // 2. Authenticate User
    const { data: { user }, error: authError } = await supabaseClient.auth.getUser(token);

    if (authError || !user) {
      console.error("[AUTH FAIL]", authError?.message || "User not found");
      return new Response(JSON.stringify({ 
        error: "Unauthorized", 
        details: "Token verification failed.",
        auth_message: authError?.message || "Invalid session",
        auth_status: authError?.status || "none"
      }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    console.log(`[AUTH SUCCESS] User ID: ${user.id}`);

    // 3. Extract Interview Params
    let body;
    try {
      body = await req.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: "Invalid JSON body" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }
    
    const { interviewId } = body;
    if (!interviewId) {
      return new Response(JSON.stringify({ error: "Missing interviewId" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 4. Verify Participation Identity
    const { data: participant, error: partError } = await supabaseClient
      .from("interview_participants")
      .select("role")
      .eq("interview_id", interviewId)
      .eq("profile_id", user.id)
      .single();

    if (partError || !participant) {
      console.error(`[FORBIDDEN] User ${user.id} is not a participant in interview ${interviewId}`);
      return new Response(JSON.stringify({ 
        error: "Forbidden: Not an interview participant",
        debug: partError?.message 
      }), {
        status: 403,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 5. Get Participant Profile Information
    const { data: profile } = await supabaseClient
      .from("profiles")
      .select("full_name")
      .eq("id", user.id)
      .single();

    // 6. Generate LiveKit Access Token
    const apiKey = Deno.env.get("LIVEKIT_API_KEY");
    const apiSecret = Deno.env.get("LIVEKIT_API_SECRET");

    if (!apiKey || !apiSecret) {
        throw new Error("LiveKit credentials not configured in environment");
    }

    const roomName = `interview-${interviewId}`;
    const participantName = profile?.full_name || user.email || "Anonymous Agent";

    const at = new AccessToken(apiKey, apiSecret, {
      identity: user.id,
      name: participantName,
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const jwt = await at.toJwt();

    return new Response(JSON.stringify({ 
      token: jwt, 
      roomName, 
      participantName,
      role: participant.role 
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });

  } catch (error) {
    console.error("[CRITICAL ERROR]", error.message);
    return new Response(JSON.stringify({ 
      error: "Internal Server Error", 
      details: error.message 
    }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});
