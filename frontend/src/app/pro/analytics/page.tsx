import { Badge } from "@/components/ui/badge";
import { BarChart3, Lock } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div className="space-y-2">
          <Badge variant="outline" className="bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800">
            <BarChart3 className="w-3 h-3 mr-1 inline-block" /> Pro Feature
          </Badge>
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-3">
            Investment Analytics
          </h1>
          <p className="text-slate-500 dark:text-slate-400 font-medium">
            Deep dive into market trends, yields, and predictions.
          </p>
        </div>
      </div>

      <div className="text-center py-20 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800 border-dashed">
        <div className="w-16 h-16 bg-amber-100 dark:bg-amber-900/30 text-amber-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Pro Tier Required</h2>
        <p className="text-slate-500 mt-2 max-w-md mx-auto">
          Investment Analytics is only available for Pro users. Upgrade your account to unlock deep market insights.
        </p>
      </div>
    </div>
  );
}
