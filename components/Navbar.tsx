"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Rocket, Zap, Users, CheckCircle } from "lucide-react";

const Navbar = () => {
    const [scrolled, setScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener("scroll", handleScroll);
        return () => window.removeEventListener("scroll", handleScroll);
    }, []);

    const navLinks = [
        { name: "Features", href: "#features", icon: <Rocket className="w-4 h-4" /> },
        { name: "How it Works", href: "#how-it-works", icon: <Zap className="w-4 h-4" /> },
        { name: "For Recruiters", href: "#recruiters", icon: <Users className="w-4 h-4" /> },
        { name: "Pricing", href: "#pricing", icon: <CheckCircle className="w-4 h-4" /> },
    ];

    return (
        <nav
            className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-500 ${
                scrolled
                    ? "bg-white/70 backdrop-blur-xl border-b border-gray-100/50 py-3"
                    : "bg-transparent py-6"
            }`}
        >
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="flex items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center space-x-3 group">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden transition-transform group-hover:scale-110">
                            <img src="/logo.png" alt="HireSight Logo" className="w-full h-full object-cover scale-[1.3]" />
                        </div>
                        <span className="font-display text-2xl font-black bg-gradient-to-r from-primary via-primary to-secondary bg-clip-text text-transparent tracking-tighter">
                            HireSight
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden lg:flex items-center space-x-1 p-1 bg-gray-100/30 backdrop-blur-md rounded-full border border-gray-200/50">
                        {navLinks.map((link) => (
                            <Link
                                key={link.name}
                                href={link.href}
                                className="px-5 py-2 text-sm font-semibold text-gray-600 hover:text-primary rounded-full hover:bg-white transition-all duration-300 flex items-center space-x-2"
                            >
                                <span>{link.name}</span>
                            </Link>
                        ))}
                    </div>

                    {/* CTA Buttons */}
                    <div className="hidden lg:flex items-center space-x-4">
                        <Link
                            href="/login"
                            className="text-sm font-bold text-gray-600 hover:text-primary transition-colors px-4"
                        >
                            Log In
                        </Link>
                        <Link
                            href="/register"
                            className="relative group overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-primary to-secondary transition-all duration-500 group-hover:scale-110" />
                            <div className="relative px-6 py-2.5 bg-transparent text-white font-bold text-sm rounded-lg flex items-center space-x-2">
                                <span>Get Started</span>
                                <Rocket className="w-4 h-4 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                            </div>
                        </Link>
                    </div>

                    {/* Mobile Menu Button */}
                    <button
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="lg:hidden p-2 text-gray-600 hover:text-primary transition-colors"
                    >
                        {mobileMenuOpen ? <X className="w-7 h-7" /> : <Menu className="w-7 h-7" />}
                    </button>
                </div>
            </div>

            {/* Mobile Menu */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        className="lg:hidden bg-white/95 backdrop-blur-2xl border-t border-gray-100 overflow-hidden shadow-2xl"
                    >
                        <div className="px-6 py-8 space-y-4">
                            {navLinks.map((link) => (
                                <Link
                                    key={link.name}
                                    href={link.href}
                                    onClick={() => setMobileMenuOpen(false)}
                                    className="block text-lg font-bold text-gray-800 hover:text-primary transition-colors flex items-center space-x-3"
                                >
                                    <div className="p-2 bg-gray-50 rounded-lg text-primary">{link.icon}</div>
                                    <span>{link.name}</span>
                                </Link>
                            ))}
                            <div className="pt-6 border-t border-gray-100 space-y-4">
                                <Link
                                    href="/login"
                                    className="block text-center py-4 rounded-2xl bg-gray-50 font-bold text-gray-700 hover:bg-gray-100 transition-all"
                                >
                                    Log In
                                </Link>
                                <Link
                                    href="/register"
                                    className="block text-center py-4 rounded-2xl bg-primary text-white font-bold shadow-xl shadow-primary/30 hover:scale-[1.02] active:scale-[0.98] transition-all"
                                >
                                    Try HireSight Free
                                </Link>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    );
};

export default Navbar;
