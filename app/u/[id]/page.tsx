import { createClient } from "@/lib/supabase/server";
import { notFound } from "next/navigation";
import FollowButton from "@/components/network/FollowButton";
import ProfileViewTracker from "@/components/network/ProfileViewTracker";
import { Globe, Briefcase, MapPin, Calendar, Award } from "lucide-react";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";

export default async function PublicProfilePage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    const supabase = await createClient();

    // Identify current user to determine viewer context
    const { data: { user } } = await supabase.auth.getUser();
    let viewerRole: string | undefined;
    
    if (user) {
         const { data: viewerProfile } = await supabase
            .from("profiles")
            .select("role")
            .eq("id", user.id)
            .single();
         viewerRole = viewerProfile?.role;
    }

    const { data: profile } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", id)
        .single();

    if (!profile) {
        notFound();
    }

    // Fetch Stats
    const [{ count: followersCount }, { count: followingCount }, { data: mutuals }] = await Promise.all([
        supabase.from("follows").select("id", { count: 'exact', head: true }).eq("following_id", id),
        supabase.from("follows").select("id", { count: 'exact', head: true }).eq("follower_id", id),
        user ? supabase.rpc('get_mutual_connections', { user_id1: user.id, user_id2: id }) : { data: [] }
    ]);

    // Format mutual connections logic safely
    const mutualCount = mutuals ? mutuals.length : 0;

    return (
        <div className="min-h-screen bg-gray-50/30 pt-32 pb-24">
            <ProfileViewTracker profileId={id} />
            <div className="max-w-4xl mx-auto px-6 space-y-12">
                 {/* Header Protocol */}
                 <div className="bg-white border border-gray-100 rounded-[48px] p-12 shadow-sm relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[80px] rounded-full pointer-events-none" />
                    
                    <div className="relative z-10 flex flex-col md:flex-row md:items-start gap-8">
                        <div className="w-32 h-32 bg-gray-50 rounded-[40px] border border-gray-100 flex items-center justify-center font-black text-6xl text-primary italic overflow-hidden shadow-xl">
                            {profile.avatar_url ? (
                                <img src={profile.avatar_url} alt={profile.full_name} className="w-full h-full object-cover" />
                            ) : (
                                <span>{profile.full_name?.charAt(0) || "?"}</span>
                            )}
                        </div>

                        <div className="flex-1 space-y-6">
                             <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                                 <div>
                                     <div className="flex items-center space-x-3 mb-2">
                                         <span className="px-3 py-1 bg-primary/10 text-primary text-[10px] font-black uppercase tracking-widest rounded-xl border border-primary/20 italic">
                                             {profile.role === 'company' ? 'Corporate Entity' : 'Candidate Node'}
                                         </span>
                                     </div>
                                     <h1 className="text-4xl md:text-5xl font-black font-display text-zinc-900 italic tracking-tighter leading-none mb-2">
                                         {profile.full_name || profile.company_name}
                                     </h1>
                                     <p className="text-xl font-bold text-gray-500 italic">
                                         {profile.headline || profile.bio || "No intelligence provided."}
                                     </p>
                                 </div>
                                 <div className="flex-shrink-0">
                                     <FollowButton 
                                        targetUserId={id} 
                                        targetUserName={profile.full_name} 
                                        currentUserRole={viewerRole} 
                                        className="px-8 py-4 text-sm w-full md:w-auto justify-center"
                                     />
                                 </div>
                             </div>

                             <div className="flex flex-wrap items-center gap-6 text-xs font-black uppercase tracking-widest text-gray-500">
                                 {profile.location && (
                                     <div className="flex items-center space-x-2">
                                         <MapPin className="w-4 h-4 text-gray-400" />
                                         <span>{profile.location}</span>
                                     </div>
                                 )}
                                 <div className="flex items-center space-x-2">
                                     <Calendar className="w-4 h-4 text-gray-400" />
                                     <span>Joined {new Date(profile.updated_at).getFullYear()}</span>
                                 </div>
                                 {profile.website && (
                                     <a href={profile.website} target="_blank" rel="noopener noreferrer" className="flex items-center space-x-2 hover:text-primary transition-colors">
                                         <Globe className="w-4 h-4" />
                                         <span>Secure Link</span>
                                     </a>
                                 )}
                             </div>

                             <div className="flex items-center space-x-8 pt-6 border-t border-gray-100">
                                 <div>
                                     <span className="text-2xl font-black text-zinc-900 italic tracking-tighter mr-2">{followersCount || 0}</span>
                                     <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Followers</span>
                                 </div>
                                 <div>
                                     <span className="text-2xl font-black text-zinc-900 italic tracking-tighter mr-2">{followingCount || 0}</span>
                                     <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Following</span>
                                 </div>
                                 {user && user.id !== id && (
                                     <div className="pl-8 border-l border-gray-200">
                                         <span className="text-xl font-black text-primary italic tracking-tighter mr-2">{mutualCount}</span>
                                         <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Mutual Connections</span>
                                     </div>
                                 )}
                             </div>
                        </div>
                    </div>
                 </div>

                 {/* Grid Content */}
                 <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                     <div className="md:col-span-2 space-y-8">
                         <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm">
                             <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary italic mb-6">Identity Narrative</h3>
                             <p className="text-sm font-bold text-gray-600 leading-relaxed italic bg-gray-50/50 p-6 rounded-3xl border border-gray-50">
                                 {profile.bio || "No narrative established for this node."}
                             </p>
                         </div>
                     </div>

                     <div className="md:col-span-1 space-y-8">
                         {profile.role === 'candidate' && profile.skills && (
                             <div className="bg-white border border-gray-100 rounded-[40px] p-10 shadow-sm">
                                 <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary italic mb-6">Verified Skills</h3>
                                 <div className="flex flex-wrap gap-2">
                                     {(profile.skills as string[]).map((skill: string) => (
                                         <span key={skill} className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-xl text-[10px] font-black uppercase tracking-widest">
                                             {skill}
                                         </span>
                                     ))}
                                 </div>
                             </div>
                         )}
                     </div>
                 </div>
            </div>
        </div>
    );
}
