"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Bookmark, Loader2, ArrowRight } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api-client";
import { useSession } from "next-auth/react";
import type { SavedLocationResponse, LocationSummary } from "@/types/api";
import { LocationSearch } from "@/components/location-search";

export function SavedLocations() {
  const { data: session } = useSession();
  const router = useRouter();
  const [locations, setLocations] = useState<SavedLocationResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [generatingId, setGeneratingId] = useState<string | null>(null);

  const fetchLocations = useCallback(async () => {
    if (!session) return;
    try {
      const data = await apiGet<SavedLocationResponse[]>("/dashboard/saved-locations", session);
      setLocations(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  useEffect(() => {
    fetchLocations();
  }, [fetchLocations]);

  const handleLocationSelect = async (location: LocationSummary) => {
    setIsLoading(true);
    try {
      await apiPost("/dashboard/saved-locations", { location_id: location.id }, session);
      await fetchLocations();
    } catch (e) {
      console.error(e);
      setIsLoading(false);
    }
  };

  const handleGenerate = async (locationId: string) => {
    setGeneratingId(locationId);
    try {
      const data = await apiPost<{id: string}, {location_id: string}>("/reports", { location_id: locationId }, session);
      router.push(`/report/${data.id}`);
    } catch (e) {
      console.error(e);
      setGeneratingId(null);
    }
  };

  return (
    <Card className="border-slate-200/60 dark:border-slate-800/60 shadow-md h-full flex flex-col">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Bookmark className="w-5 h-5 text-indigo-500" />
          Saved Locations
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1 overflow-auto max-h-[500px]">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800">
          <LocationSearch onLocationSelect={handleLocationSelect} placeholder="Search to save location..." />
        </div>
        {isLoading ? (
          <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
        ) : locations.length === 0 ? (
          <div className="text-center text-slate-500 dark:text-slate-400 p-8">
            You haven&apos;t saved any locations yet. Search above to add one.
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {locations.map(loc => (
              <div key={loc.id} className="p-4 hover:bg-slate-50 dark:hover:bg-slate-900/30 transition-colors flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-slate-900 dark:text-white">
                    {loc.location.suburb || loc.location.city}
                  </h4>
                  <p className="text-xs text-slate-500">
                    {loc.location.state} {loc.location.postcode}
                  </p>
                </div>
                <Button 
                  size="sm" 
                  variant="ghost" 
                  onClick={() => handleGenerate(loc.location.id)}
                  disabled={generatingId === loc.location.id}
                  className="text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50"
                >
                  {generatingId === loc.location.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>Generate <ArrowRight className="w-4 h-4 ml-1" /></>
                  )}
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
