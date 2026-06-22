"use client";

import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";

export default function Home() {
  const router = useRouter();
  const { status } = useSession();

  const handleAnalyze = () => {
    // Signed-in users go straight to the report flow; otherwise send them to
    // login first, returning to the report flow afterwards.
    if (status === "authenticated") {
      router.push("/report/new");
    } else {
      router.push(`/login?callbackUrl=${encodeURIComponent("/report/new")}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 relative overflow-hidden bg-slate-50 dark:bg-slate-950">
      {/* Decorative background gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-blue-500/20 blur-[120px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="max-w-3xl w-full text-center space-y-8 z-10"
      >
        <div className="space-y-4">
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 text-sm font-medium mb-4"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            AI-Powered Real Estate Intelligence
          </motion.div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Instant Insights for <br/>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500">
              Smarter Decisions
            </span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Generate professional-grade market reports instantly. Analyze trends, pricing, demographics, and investment potential with Gemini AI.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
          className="mt-12 flex justify-center"
        >
          <Button
            size="lg"
            onClick={handleAnalyze}
            className="h-14 px-10 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-lg transition-all shadow-lg shadow-indigo-500/20"
          >
            Analyze Market
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          className="pt-12 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-slate-500 dark:text-slate-400"
        >
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-indigo-500 text-2xl">📈</div>
            <span className="font-medium">Market Trends</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-blue-500 text-2xl">💰</div>
            <span className="font-medium">Pricing Insights</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-emerald-500 text-2xl">🏙️</div>
            <span className="font-medium">Neighborhoods</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="w-12 h-12 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-purple-500 text-2xl">🤖</div>
            <span className="font-medium">AI Summaries</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}
