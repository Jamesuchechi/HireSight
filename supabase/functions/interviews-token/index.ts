import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { AccessToken } from "npm:livekit-server-sdk";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("NEXT_PUBLIC_SUPABASE_URL") ?? "",
      Deno.env.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") ?? "",
      {
        global: {
          headers: { Authorization: req.headers.get("Authorization")! },
        },
      }
    );

    // 1. Get User
    const {
      data: { user },
      error: authError,
    } = await supabaseClient.auth.getUser();

    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
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
