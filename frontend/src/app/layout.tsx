import type { Metadata } from "next";
import "./globals.css";
import { Inter } from "next/font/google";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Building2 } from "lucide-react";

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' });

import { Providers } from "./providers";
import { AuthNav } from "@/components/auth-nav";

export const metadata: Metadata = {
  title: "Cotality Intelligence | AI Real Estate",
  description: "AI-Powered Real Estate Intelligence Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={cn("font-sans", inter.variable)}>
      <body className="min-h-screen bg-slate-50 antialiased dark:bg-slate-950 flex flex-col text-slate-900 dark:text-slate-50">
        <Providers>
          <header className="sticky top-0 z-50 w-full border-b border-slate-200/60 bg-white/80 backdrop-blur-md dark:bg-slate-950/80 dark:border-slate-800">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
              <Link href="/" className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-xl tracking-tight transition-transform hover:scale-105">
                <Building2 className="w-6 h-6" />
                <span>Cotality Intelligence</span>
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
