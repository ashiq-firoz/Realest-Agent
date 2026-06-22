"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import { apiGet, apiPost } from "@/lib/api-client";
import { useSession } from "next-auth/react";
import { Activity, Loader2 } from "lucide-react";
import type { WatchlistEntryResponse, LocationSummary } from "@/types/api";
import { LocationSearch } from "@/components/location-search";

export function WatchlistPanel() {
  const { data: session } = useSession();
  const [entries, setEntries] = useState<WatchlistEntryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchWatchlist = useCallback(async () => {
    if (!session) return;
    try {
      const data = await apiGet<WatchlistEntryResponse[]>("/watchlist", session);
      setEntries(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const handleLocationSelect = async (location: LocationSummary) => {
    setIsLoading(true);
    try {
      await apiPost("/watchlist", { location_id: location.id }, session);
      await fetchWatchlist();
    } catch (e) {
      console.error(e);
      setIsLoading(false);
    }
  };

  return (
    <Card className="col-span-full xl:col-span-2 border-slate-200/60 dark:border-slate-800/60 shadow-md flex flex-col h-full">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Activity className="w-5 h-5 text-indigo-500" />
          Market Watchlist
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0 flex-1 overflow-auto max-h-[500px]">
        <div className="p-4 border-b border-slate-100 dark:border-slate-800">
          <LocationSearch onLocationSelect={handleLocationSelect} placeholder="Search to add to watchlist..." />
        </div>
        {isLoading ? (
          <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
        ) : entries.length === 0 ? (
          <div className="text-center text-slate-500 dark:text-slate-400 py-8">
            No properties in your watchlist. Search above to add locations and track market trends.
          </div>
        ) : (
          <div className="grid gap-6 p-6 md:grid-cols-2 lg:grid-cols-3">
            {entries.map(entry => (
              <div key={entry.id} className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/30">
                <h4 className="font-semibold text-slate-900 dark:text-white mb-4 truncate" title={entry.location.display_name}>
                  {entry.location.suburb || entry.location.city}
                </h4>
                <div className="h-[60px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={entry.price_history?.map(price => ({ value: price })) ?? []}>
                      <YAxis domain={['auto', 'auto']} hide />
                      <Tooltip contentStyle={{ fontSize: '12px', borderRadius: '8px' }} labelStyle={{ display: 'none' }} />
                      <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
