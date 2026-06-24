import type { Metadata } from "next";
import "./globals.css";
import { Plus_Jakarta_Sans, Newsreader } from "next/font/google";
import { cn } from "@/lib/utils";
import Link from "next/link";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const newsreader = Newsreader({
  subsets: ["latin"],
  variable: "--font-newsreader",
  display: "swap",
});

import { Providers } from "./providers";
import { AuthNav } from "@/components/auth-nav";

export const metadata: Metadata = {
  title: "Estately AI | Market Intelligence",
  description: "AI-Powered Real Estate Market Intelligence Platform — Generate professional-grade market reports instantly.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", jakarta.variable, newsreader.variable)}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-background antialiased flex flex-col text-on-surface">
        <Providers>
          <header className="sticky top-0 z-50 w-full bg-surface/95 backdrop-blur-md border-b border-outline-variant">
            <div className="container mx-auto px-container-margin h-16 flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2 text-primary font-bold text-headline-md font-headline-md tracking-tight transition-transform hover:scale-105">
                <span className="material-symbols-outlined text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                <span>Estately AI</span>
              </Link>
              <AuthNav />
            </div>
          </header>
          <main className="flex-1 flex flex-col">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
