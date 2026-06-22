"use client";

import Link from "next/link";
import { Lock } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ProUpgradePromptProps {
  featureName: string;
}

export function ProUpgradePrompt({ featureName }: ProUpgradePromptProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-slate-50 to-indigo-50/30 dark:from-slate-900/50 dark:to-indigo-950/20 rounded-xl border border-indigo-100 dark:border-indigo-900/50">
      <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/50 rounded-full flex items-center justify-center mb-4">
        <Lock className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
        {featureName} is a Pro feature
      </h3>
      <p className="text-sm text-slate-500 dark:text-slate-400 max-w-sm mb-6">
        Upgrade to Cotality Intelligence Pro to unlock advanced analytics, real-time market tracking, and unlimited reporting capabilities.
      </p>
      <Link href="/pricing">
        <Button className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium">
          Upgrade to Pro
        </Button>
      </Link>
    </div>
  );
}
