import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HireSight 2.0 - AI-Powered Recruitment",
  description: "Next Generation Recruitment with Next.js 15 & Supabase",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700;800&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased selection:bg-primary/20 selection:text-primary">
        {children}
      </body>
    </html>
  );
}
