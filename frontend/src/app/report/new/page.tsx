"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
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
    <div className="flex-1 flex flex-col items-center justify-center min-h-[80vh] bg-background px-container-margin">
      <div className="w-full max-w-xl space-y-lg">
        <div className="text-center space-y-sm">
          <div className="mx-auto w-16 h-16 rounded-2xl bg-primary-container/30 flex items-center justify-center">
            <span className="material-symbols-outlined text-primary text-3xl">query_stats</span>
          </div>
          <h1 className="text-headline-lg font-headline-lg font-serif text-on-surface">
            Generate Intelligence Report
          </h1>
          <p className="text-body-md font-body-md text-on-surface-variant max-w-md mx-auto">
            Search for an Australian location to uncover deep market insights, demographics, and AI-driven intelligence.
          </p>
        </div>

        <div className="tonal-card p-lg rounded-2xl space-y-lg">
          <div className="space-y-xs">
            <label className="text-label-sm font-label-sm text-on-surface-variant ml-xs">
              Location
            </label>
            <LocationSearch 
              onLocationSelect={setSelectedLocation} 
              placeholder="Start typing a suburb or postcode..." 
              autoFocus 
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 text-label-sm font-label-sm text-error bg-error-container/30 rounded-xl p-md border border-error/20">
              <span className="material-symbols-outlined text-[18px]">error</span>
              {error}
            </div>
          )}

          <Button
            onClick={handleGenerate}
            disabled={!selectedLocation || isGenerating}
            className="w-full py-4 text-label-md font-label-md bg-primary-container text-on-primary-container hover:opacity-90 active:scale-95 transition-all rounded-xl shadow-md h-auto"
          >
            {isGenerating ? (
              <>
                <span className="material-symbols-outlined text-[18px] animate-spin mr-2">progress_activity</span>
                Analyzing market data...
              </>
            ) : (
              <>
                Generate Report
                <span className="material-symbols-outlined text-[18px] ml-2">trending_up</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
