"use client";

import React from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter();
  const { status } = useSession();
  const [query, setQuery] = React.useState("");

  const handleAskAgent = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (status === "authenticated") {
      router.push(`/agent?q=${encodeURIComponent(query)}`);
    } else {
      if (query.trim() !== "") {
        // Pass query to signup, so after signup they get redirected with query
        router.push(`/login?callbackUrl=${encodeURIComponent(`/agent?q=${encodeURIComponent(query)}`)}`);
      } else {
        router.push(`/login?callbackUrl=${encodeURIComponent("/agent")}`);
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-background overflow-hidden">
      <div className="max-w-5xl mx-auto w-full px-container-margin">
        {/* Hero Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="py-xl flex flex-col gap-md"
        >
          <div className="flex flex-col gap-xs">
            <span className="text-label-md font-label-md text-tertiary uppercase tracking-widest">
              AI Real Estate Agent
            </span>
            <h1 className="text-display-lg font-display-lg text-on-surface leading-tight">
              Meet your AI <span className="text-primary">Property Expert</span>
            </h1>
          </div>
          <p className="text-body-lg font-body-lg text-on-surface-variant max-w-xl">
            Ask anything about the Australian property market. Discover listings, analyze suburbs, compare agents, and generate instant intelligence reports.
          </p>

          <form onSubmit={handleAskAgent} className="mt-8 relative max-w-2xl flex flex-col gap-4">
            <div className="relative flex items-center">
              <span className="material-symbols-outlined absolute left-4 text-on-surface-variant">
                chat
              </span>
              <input
                type="text"
                placeholder="Find 3-bedroom houses under $800k in Brisbane..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 rounded-xl border border-outline-variant bg-surface-container focus:outline-none focus:ring-2 focus:ring-primary text-body-lg text-on-surface shadow-sm"
              />
            </div>
            <div className="flex gap-4">
              <Button
                type="submit"
                className="bg-primary text-on-primary font-label-md text-label-md py-6 px-8 rounded-xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md flex-1 sm:flex-none"
              >
                Ask Agent
                <span className="material-symbols-outlined">send</span>
              </Button>
              <Button
                type="button"
                onClick={() =>
                  router.push(
                    status === "authenticated"
                      ? "/agent"
                      : `/login?callbackUrl=${encodeURIComponent("/agent")}`
                  )
                }
                variant="outline"
                className="py-6 px-8 rounded-xl flex items-center justify-center gap-2"
              >
                Go to Chat
                <span className="material-symbols-outlined">arrow_forward</span>
              </Button>
            </div>
          </form>
        </motion.section>

        {/* Bento Features Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="py-lg grid grid-cols-1 gap-md"
        >
          <h3 className="text-headline-md font-headline-md text-on-surface font-serif">
            Capabilities
          </h3>
          <div className="grid grid-cols-2 gap-md">
            {/* Market Trends */}
            <div className="tonal-card p-md rounded-2xl flex flex-col gap-sm hover:active-glow transition-shadow duration-300">
              <span className="material-symbols-outlined text-primary">search</span>
              <p className="text-label-md font-label-md">Property Search</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">Real-time listings across AU.</p>
            </div>
            {/* Pricing Insights */}
            <div className="tonal-card p-md rounded-2xl flex flex-col gap-sm hover:active-glow transition-shadow duration-300">
              <span className="material-symbols-outlined text-primary">analytics</span>
              <p className="text-label-md font-label-md">Data Analysis</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">Historical sales & suburb intel.</p>
            </div>
          </div>

          {/* Neighborhoods (Full Width) */}
          <div className="tonal-card p-md rounded-2xl flex items-center justify-between sage-accent hover:active-glow transition-shadow duration-300">
            <div className="flex flex-col gap-xs">
              <p className="text-label-md font-label-md">Agent Comparison</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">Find top performing local agents.</p>
            </div>
            <span className="material-symbols-outlined text-tertiary">groups</span>
          </div>
        </motion.section>

        {/* CTA / Footer Branding */}
        <motion.section
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.8 }}
          className="py-xl mb-12 text-center flex flex-col items-center gap-md"
        >
          <div className="h-px w-24 bg-outline-variant" />
          <p className="text-headline-lg font-headline-lg italic text-primary font-serif">
            The AI-First Agent Platform
          </p>
          <p className="text-label-md font-label-md text-on-surface-variant">
            © 2026 Novestate. All rights reserved.
          </p>
        </motion.section>
      </div>
    </div>
  );
}
