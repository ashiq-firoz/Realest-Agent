"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter();
  const { status } = useSession();

  const handleAnalyze = () => {
    if (status === "authenticated") {
      router.push("/report/new");
    } else {
      router.push(`/login?callbackUrl=${encodeURIComponent("/report/new")}`);
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
              AI Market Intelligence
            </span>
            <h1 className="text-display-lg font-display-lg text-on-surface leading-tight">
              Instant Insights for{" "}
              <span className="text-primary">Smarter Decisions</span>
            </h1>
          </div>
          <p className="text-body-lg font-body-lg text-on-surface-variant max-w-xl">
            Generate professional-grade market reports instantly. Analyze trends,
            pricing, and investment potential with Gemini AI.
          </p>
          <div className="flex flex-col sm:flex-row gap-md pt-sm">
            <Button
              onClick={handleAnalyze}
              className="bg-primary-container text-on-primary-container font-label-md text-label-md py-4 px-xl rounded-xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md h-auto"
            >
              Analyze Market
              <span className="material-symbols-outlined">trending_up</span>
            </Button>
          </div>
        </motion.section>

        {/* Image Reference Section */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.8 }}
          className="py-lg"
        >
          <div className="relative rounded-2xl overflow-hidden tonal-card p-2">
            <div className="aspect-[2.19/1] w-full rounded-xl overflow-hidden bg-surface-container">
              {/* <img
                alt="Platform UI Overview"
                className="w-full h-full object-cover"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuD8cCIGzjFWc5PGVF-CXBoq1sAoVE9xwjxhy0XSzWrVXexLKA011vLhkW1bSv_WQ6ibDVgZI-CbJTSOF2Q1QSmfDpLJHEqZs7gMpewUkkIXgQoFIjAW4n_EGcrAWUTj0ARtLArteoALFO-QPz-TzKPfZgoLeJaYYpEXp5mtGrhToq35NxZCb73OniGhz1Iz75SG_Pzqjwh0FApxQ3brcipihBEnwvPE9ln8hWL_hZfXmBrSQPnmO8LjYFTREfb84j9_EbGUDRZF-Go"
              /> */}
            </div>
            <div className="absolute bottom-4 left-4 right-4 bg-surface/90 backdrop-blur-md p-md rounded-xl border border-outline-variant">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-tertiary/10 flex items-center justify-center text-tertiary">
                  <span className="material-symbols-outlined">query_stats</span>
                </div>
                <div>
                  <p className="text-label-md font-label-md text-on-surface">Live Market Feed</p>
                  <p className="text-label-sm font-label-sm text-on-surface-variant">
                    Gemini AI is processing 42 new listings...
                  </p>
                </div>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Bento Features Grid */}
        <motion.section
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.8 }}
          className="py-lg grid grid-cols-1 gap-md"
        >
          <h3 className="text-headline-md font-headline-md text-on-surface font-serif">
            Core Intelligence
          </h3>
          <div className="grid grid-cols-2 gap-md">
            {/* Market Trends */}
            <div className="tonal-card p-md rounded-2xl flex flex-col gap-sm hover:active-glow transition-shadow duration-300">
              <span className="material-symbols-outlined text-primary">analytics</span>
              <p className="text-label-md font-label-md">Market Trends</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">Real-time velocity tracking.</p>
            </div>
            {/* Pricing Insights */}
            <div className="tonal-card p-md rounded-2xl flex flex-col gap-sm hover:active-glow transition-shadow duration-300">
              <span className="material-symbols-outlined text-primary">payments</span>
              <p className="text-label-md font-label-md">Pricing Insights</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">AI-driven valuation models.</p>
            </div>
          </div>

          {/* Neighborhoods (Full Width) */}
          <div className="tonal-card p-md rounded-2xl flex items-center justify-between sage-accent hover:active-glow transition-shadow duration-300">
            <div className="flex flex-col gap-xs">
              <p className="text-label-md font-label-md">Neighborhoods</p>
              <p className="text-label-sm font-label-sm text-on-surface-variant">Hyper-local growth analytics per block.</p>
            </div>
            <span className="material-symbols-outlined text-tertiary">location_city</span>
          </div>

          {/* AI Summaries (Full Width with emphasis) */}
          <div className="bg-tertiary-container/30 border border-tertiary-container p-md rounded-2xl flex flex-col gap-sm">
            <div className="flex items-center gap-2 text-tertiary">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
              <p className="text-label-md font-label-md">AI Summaries</p>
            </div>
            <p className="text-body-md font-body-md text-on-tertiary-container italic">
              &ldquo;This zip code is experiencing a 14% uptick in investor interest due to the upcoming tech hub completion.&rdquo;
            </p>
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
            Trust the Data. Own the Future.
          </p>
          <p className="text-label-md font-label-md text-on-surface-variant">
            © 2024 Estately AI. All rights reserved.
          </p>
        </motion.section>
      </div>
    </div>
  );
}
