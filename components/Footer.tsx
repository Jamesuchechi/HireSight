"use client";

import Link from "next/link";
import { Github, Twitter, Linkedin, Rocket } from "lucide-react";

const Footer = () => {
    return (
        <footer className="bg-gray-50 border-t border-gray-100 py-20">
            <div className="max-w-7xl mx-auto px-6 lg:px-8">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
                    {/* Brand Section */}
                    <div className="md:col-span-1">
                        <Link href="/" className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 rounded-xl flex items-center justify-center overflow-hidden transition-transform group-hover:scale-110">
                                <img src="/logo.png" alt="HireSight Logo" className="w-full h-full object-cover scale-[1.3]" />
                            </div>
                            <span className="font-display text-2xl font-black bg-gradient-to-r from-primary via-primary to-secondary bg-clip-text text-transparent tracking-tighter">
                                HireSight
                            </span>
                        </Link>
                        <p className="text-gray-500 font-medium mb-6">
                            The future of intelligent recruitment. Building fairer, faster, and more efficient hiring cycles for the top 1%.
                        </p>
                        <div className="flex items-center space-x-4">
                            <Link href="#" className="p-2 bg-white border border-gray-100 rounded-lg text-gray-400 hover:text-primary transition-all shadow-sm">
                                <Twitter className="w-5 h-5" />
                            </Link>
                            <Link href="#" className="p-2 bg-white border border-gray-100 rounded-lg text-gray-400 hover:text-primary transition-all shadow-sm">
                                <Linkedin className="w-5 h-5" />
                            </Link>
                            <Link href="#" className="p-2 bg-white border border-gray-100 rounded-lg text-gray-400 hover:text-primary transition-all shadow-sm">
                                <Github className="w-5 h-5" />
                            </Link>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h4 className="text-zinc-900 font-black uppercase text-xs tracking-widest mb-6">Platform</h4>
                        <ul className="space-y-4">
                            {["AI Matching", "Bias-Free Screening", "Kanban Pipeline", "Messaging"].map((item) => (
                                <li key={item}>
                                    <Link href="#" className="text-gray-500 font-bold hover:text-primary transition-colors">{item}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-zinc-900 font-black uppercase text-xs tracking-widest mb-6">Resources</h4>
                        <ul className="space-y-4">
                            {["Documentation", "API Reference", "Status", "Contact Support"].map((item) => (
                                <li key={item}>
                                    <Link href="#" className="text-gray-500 font-bold hover:text-primary transition-colors">{item}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-zinc-900 font-black uppercase text-xs tracking-widest mb-6">Legal</h4>
                        <ul className="space-y-4">
                            {["Privacy Policy", "Terms of Service", "Cookie Policy", "Data Processing"].map((item) => (
                                <li key={item}>
                                    <Link href="#" className="text-gray-500 font-bold hover:text-primary transition-colors">{item}</Link>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                <div className="pt-8 border-t border-gray-200/50 flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
                    <p className="text-sm font-bold text-gray-400">
                        &copy; 2026 HireSight 2.0 AI. All rights reserved. Built with Next.js 16.
                    </p>
                    <div className="flex items-center space-x-6 text-sm font-bold text-gray-400">
                        <Link href="#" className="hover:text-primary transition-colors">Twitter</Link>
                        <Link href="#" className="hover:text-primary transition-colors">LinkedIn</Link>
                        <Link href="#" className="hover:text-primary transition-colors">Discord</Link>
                    </div>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
