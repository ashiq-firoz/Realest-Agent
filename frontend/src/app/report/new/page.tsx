"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { Building2, Loader2, AlertCircle } from "lucide-react";
import { LocationSearch } from "@/components/location-search";
import { Button } from "@/components/ui/button";
import { apiPost } from "@/lib/api-client";
import type { LocationSummary, ReportResponse } from "@/types/api";

export default function NewReportPage() {
  const router = useRouter();
  const { data: session } = useSession();
  const [selectedLocation, setSelectedLocation] = useState<LocationSummary | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!selectedLocation) return;
    
    setIsGenerating(true);
    setError(null);

    try {
      const report = await apiPost<ReportResponse, { location_id: string }>(
        "/reports",
        { location_id: selectedLocation.id },
        session
      );
      
      router.push(`/report/${report.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to generate report. Please try again.");
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh] bg-slate-50 dark:bg-slate-950 px-4">
      <div className="w-full max-w-xl space-y-8">
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
            <Building2 className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Generate Intelligence Report
          </h1>
          <p className="text-slate-500 dark:text-slate-400">
            Search for an Australian location to uncover deep market insights, demographics, and AI-driven intelligence.
          </p>
        </div>

        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Location
            </label>
            <LocationSearch 
              onLocationSelect={setSelectedLocation} 
              placeholder="Start typing a suburb or postcode..." 
              autoFocus 
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg p-3 border border-red-200 dark:border-red-900">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              {error}
            </div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={!selectedLocation || isGenerating}
            className="w-full h-12 text-base font-semibold bg-indigo-600 hover:bg-indigo-700 text-white transition-all"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                Analyzing market data...
              </>
            ) : (
              "Generate Report"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
