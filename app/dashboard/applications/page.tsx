"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import CandidateApplications from "@/components/dashboard/CandidateApplications";
import RecruiterApplications from "@/components/dashboard/RecruiterApplications";
import { motion, AnimatePresence } from "framer-motion";

export default function ApplicationsPage() {
    const supabase = createClient();
    const [role, setRole] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRole = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) return;

            const { data: profile } = await supabase
                .from("profiles")
                .select("role")
                .eq("id", user.id)
                .single();

            if (profile) setRole(profile.role);
            setLoading(false);
        };

        fetchRole();
    }, [supabase]);

    if (loading) return (
        <div className="flex items-center justify-center min-h-[400px]">
             <div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
    );

    return (
        <div className="max-w-7xl mx-auto pb-20">
            <AnimatePresence mode="wait">
                <motion.div
                    key={role}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                >
                    {role === "recruiter" ? (
                        <RecruiterApplications />
                    ) : (
                        <CandidateApplications />
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
