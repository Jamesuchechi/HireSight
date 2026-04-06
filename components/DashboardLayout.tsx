"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
    LayoutDashboard, 
    Briefcase, 
    Users, 
    FileText, 
    Settings, 
    LogOut, 
    Bell, 
    Search, 
    Menu, 
    X,
    TrendingUp,
    Zap,
    MapPin,
    ArrowUpRight
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

interface NavItem {
    label: string;
    href: string;
    icon: React.ReactNode;
}

const candidateNav: NavItem[] = [
    { label: "Overview", href: "/dashboard", icon: <LayoutDashboard className="w-5 h-5" /> },
    { label: "Job Search", href: "/dashboard/jobs", icon: <Search className="w-5 h-5" /> },
    { label: "Applications", href: "/dashboard/applications", icon: <FileText className="w-5 h-5" /> },
    { label: "My Profile", href: "/dashboard/profile", icon: <Users className="w-5 h-5" /> },
    { label: "Settings", href: "/dashboard/settings", icon: <Settings className="w-5 h-5" /> },
];

const recruiterNav: NavItem[] = [
    { label: "Overview", href: "/dashboard", icon: <LayoutDashboard className="w-5 h-5" /> },
    { label: "Active Jobs", href: "/dashboard/jobs/manage", icon: <Briefcase className="w-5 h-5" /> },
    { label: "Candidates", href: "/dashboard/candidates", icon: <Users className="w-5 h-5" /> },
    { label: "AI Screening", href: "/dashboard/screening", icon: <Zap className="w-5 h-5" /> },
    { label: "Settings", href: "/dashboard/settings", icon: <Settings className="w-5 h-5" /> },
];

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();
    const supabase = createClient();
    
    const [role, setRole] = useState<"candidate" | "recruiter" | null>(null);
    const [profile, setProfile] = useState<any>(null);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProfile = async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) {
                router.push("/login");
                return;
            }

            const { data: profile } = await supabase
                .from("profiles")
                .select("*")
                .eq("id", user.id)
                .single();

            if (profile) {
                setRole(profile.role);
                setProfile(profile);
            }
            setLoading(false);
        };

        fetchProfile();
    }, [router, supabase]);

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        router.push("/login");
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                    className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full"
                />
            </div>
        );
    }

    const navItems = role === "recruiter" ? recruiterNav : candidateNav;

    return (
        <div className="min-h-screen bg-gray-50 flex overflow-hidden selection:bg-primary/20 selection:text-primary">
            {/* Sidebar */}
            <aside 
                className={`fixed lg:relative z-30 h-screen bg-zinc-900 text-white transition-all duration-300 ease-in-out flex flex-col ${
                    sidebarOpen ? "w-72" : "w-20"
                } ${sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
            >
                {/* Logo Section */}
                <div className="p-6 flex items-center justify-between mb-8">
                    <Link href="/dashboard" className="flex items-center space-x-3 overflow-hidden">
                        <div className="w-10 h-10 min-w-[40px] rounded-xl overflow-hidden shadow-2xl bg-white/10 p-1">
                             <img src="/logo.png" alt="HireSight" className="w-full h-full object-cover scale-[1.3]" />
                        </div>
                        {sidebarOpen && (
                            <span className="font-display text-xl font-black tracking-widest text-white whitespace-nowrap">HIRESIGHT</span>
                        )}
                    </Link>
                    <button 
                        onClick={() => setSidebarOpen(!sidebarOpen)}
                        className="hidden lg:flex p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400"
                    >
                        {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </button>
                </div>

                {/* Navigation Items */}
                <nav className="flex-grow px-4 space-y-2 overflow-y-auto scrollbar-hide">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link 
                                key={item.href}
                                href={item.href}
                                className={`flex items-center space-x-3 px-4 py-3.5 rounded-2xl transition-all group ${
                                    isActive 
                                    ? "bg-primary text-white shadow-lg shadow-primary/20" 
                                    : "text-gray-400 hover:text-white hover:bg-white/5"
                                }`}
                            >
                                <div className={`${isActive ? "text-white" : "text-gray-500 group-hover:text-primary"} transition-colors`}>
                                    {item.icon}
                                </div>
                                {sidebarOpen && (
                                    <span className="font-bold text-sm tracking-tight">{item.label}</span>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* Footer Section (Sidebar) */}
                <div className="p-4 mt-auto border-t border-white/5">
                    <button 
                        onClick={handleSignOut}
                        className="w-full flex items-center space-x-3 px-4 py-3.5 rounded-2xl text-gray-400 hover:text-red-400 hover:bg-red-400/5 transition-all group"
                    >
                        <LogOut className="w-5 h-5" />
                        {sidebarOpen && <span className="font-bold text-sm tracking-tight">Logout</span>}
                    </button>
                    
                    {/* User Profile Summary */}
                    {sidebarOpen && (
                        <div className="mt-4 p-4 bg-white/5 rounded-[24px] flex items-center space-x-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center font-black text-white">
                                {profile?.full_name?.[0] || 'U'}
                            </div>
                            <div className="overflow-hidden">
                                <p className="text-xs font-black truncate">{profile?.full_name}</p>
                                <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest truncate">{role}</p>
                            </div>
                        </div>
                    )}
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-grow flex flex-col h-screen overflow-hidden">
                {/* Header */}
                <header className="h-20 bg-white border-b border-gray-100 flex items-center justify-between px-8 shrink-0">
                    <div className="flex items-center space-x-4">
                        <button 
                            onClick={() => setSidebarOpen(true)}
                            className="lg:hidden p-2 hover:bg-gray-50 rounded-xl"
                        >
                            <Menu className="w-6 h-6 text-gray-600" />
                        </button>
                        <div>
                             <h2 className="text-xl font-black text-zinc-900 italic tracking-tight">
                                {navItems.find(item => item.href === pathname)?.label || 'Dashboard'}
                             </h2>
                             <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none mt-1">HireSight v2.0</p>
                        </div>
                    </div>

                    <div className="flex items-center space-x-6">
                        {/* Search Bar */}
                        <div className="hidden md:flex items-center bg-gray-100 rounded-2xl px-4 py-2.5 w-64 group focus-within:bg-white focus-within:ring-2 focus-within:ring-primary/10 transition-all border border-transparent focus-within:border-primary/20">
                            <Search className="w-4 h-4 text-gray-400 mr-2" />
                            <input 
                                type="text" 
                                placeholder="Universal search..." 
                                className="bg-transparent border-none outline-none text-sm font-bold placeholder:text-gray-400 w-full"
                            />
                        </div>

                        {/* Notifications */}
                        <button className="relative p-2.5 bg-white border border-gray-100 rounded-2xl hover:bg-gray-50 transition-all shadow-sm">
                            <Bell className="w-5 h-5 text-gray-500" />
                            <span className="absolute top-2 right-2.5 w-2 h-2 bg-primary rounded-full border-2 border-white" />
                        </button>

                        <div className="h-8 w-px bg-gray-100" />

                        {/* Role Switcher or Upgrade CTA */}
                        {role === "candidate" ? (
                             <button className="hidden sm:flex items-center space-x-2 px-5 py-2.5 bg-zinc-900 text-white rounded-2xl text-xs font-black italic hover:scale-105 transition-all shadow-lg">
                                <span>Go Pro</span>
                            </button>
                        ) : (
                             <button className="hidden sm:flex items-center space-x-2 px-5 py-2.5 bg-primary text-white rounded-2xl text-xs font-black italic hover:scale-105 transition-all shadow-lg">
                                <span>Post Job</span>
                            </button>
                        )}
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-grow overflow-y-auto p-8 scrollbar-hide">
                    {children}
                </main>
            </div>
        </div>
    );
}
