import { serve } from "std/http/server.ts";
import { AccessToken } from "npm:livekit-server-sdk";
import { createClient } from "@supabase/supabase-js";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const authHeader = req.headers.get("Authorization") || req.headers.get("authorization");
    const apiKeyHeader = req.headers.get("apikey") || req.headers.get("x-api-key");
    
    // Forensic Logging (Safe)
    console.log(`[AUTH] Authorization Header: ${authHeader ? 'Present (' + authHeader.length + ' chars)' : 'MISSING'}`);
    console.log(`[AUTH] Apikey Header: ${apiKeyHeader ? 'Present (' + apiKeyHeader.slice(0, 10) + '...)' : 'MISSING'}`);

    if (!authHeader) {
      return new Response(JSON.stringify({ 
        error: "Missing Authorization header",
        details: "Expected 'Bearer <JWT>' in the Authorization header. Check if the Supabase client is sending the session token." 
      }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const token = authHeader.replace("Bearer ", "");
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      {
        global: {
          headers: { Authorization: authHeader },
        },
      }
    );
    
    // 1. Get User via explicit token check
    const {
      data: { user },
      error: authError,
    } = await supabaseClient.auth.getUser(token);

    if (authError || !user) {
      console.error("Auth Fail:", authError?.message || "No user found");
      return new Response(JSON.stringify({ 
        error: "Unauthorized: Invalid or expired token", 
        details: authError?.message || "The provided JWT could not be verified by Supabase Auth.",
        systemError: authError?.message
      }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }


    // 2. Extract Params
    const { interviewId } = await req.json();

    if (!interviewId) {
      return new Response(JSON.stringify({ error: "Missing interviewId" }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 3. Verify Participation
    const { data: participant, error: partError } = await supabaseClient
      .from("interview_participants")
      .select("role")
      .eq("interview_id", interviewId)
      .eq("profile_id", user.id)
      .single();

    if (partError || !participant) {
      return new Response(JSON.stringify({ error: "Forbidden: Not an interview participant" }), {
        status: 403,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // 4. Get Profile Info
    const { data: profile } = await supabaseClient
      .from("profiles")
      .select("full_name")
      .eq("id", user.id)
      .single();

    // 5. Generate Token
    const apiKey = Deno.env.get("LIVEKIT_API_KEY");
    const apiSecret = Deno.env.get("LIVEKIT_API_SECRET");

    if (!apiKey || !apiSecret) {
        throw new Error("LiveKit credentials not configured");
    }

    const roomName = `interview-${interviewId}`;
    const participantName = profile?.full_name || user.email || "Anonymous";

    const at = new AccessToken(apiKey, apiSecret, {
      identity: user.id, // Use user ID for stable identity
      name: participantName,
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
    });

    const token = await at.toJwt();

    return new Response(JSON.stringify({ token, roomName, participantName }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 500,
    });
  }
});
