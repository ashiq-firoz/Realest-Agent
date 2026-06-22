"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Loader2, Sparkles } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from "recharts";
import { apiGet } from "@/lib/api-client";
import { useSession } from "next-auth/react";
import type { InvestmentAnalyticsEntry } from "@/types/api";

export function InvestmentAnalytics() {
  const { data: session } = useSession();
  const [analytics, setAnalytics] = useState<InvestmentAnalyticsEntry[]>([]);
  const [insight, setInsight] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAnalytics = useCallback(async () => {
    if (!session) return;
    try {
      const [data, insightData] = await Promise.all([
        apiGet<InvestmentAnalyticsEntry[]>("/dashboard/analytics", session),
        apiGet<{insight: string}>("/dashboard/analytics/insights", session).catch(() => ({ insight: "Failed to generate insights." }))
      ]);
      setAnalytics(data);
      setInsight(insightData.insight);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const chartData = analytics.map(item => {
    const parsePercent = (val?: string) => {
      if (!val) return 0;
      const num = parseFloat(val.replace("%", "").replace(",", ""));
      return isNaN(num) ? 0 : num;
    };
    return {
      name: item.location.suburb || item.location.city,
      roi: parsePercent(item.roi_estimate),
      yield: parsePercent(item.rental_yield),
      original: item
    };
  });

  return (
    <Card className="col-span-full xl:col-span-2 border-slate-200/60 dark:border-slate-800/60 shadow-md">
      <CardHeader className="border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="w-5 h-5 text-indigo-500" />
          Top Investment Opportunities
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
        ) : analytics.length === 0 ? (
          <div className="text-center text-slate-500 dark:text-slate-400 p-8">
            Not enough data. Save locations to see investment analytics.
          </div>
        ) : (
          <div className="space-y-8">
            {insight && (
              <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl border border-indigo-100 dark:border-indigo-800/30">
                <div className="flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
                  <div className="text-sm text-slate-800 dark:text-slate-200 whitespace-pre-wrap">
                    {insight}
                  </div>
                </div>
              </div>
            )}
            
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} vertical={false} />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} tickFormatter={(val) => `${val}%`} />
                  <RechartsTooltip 
                    cursor={{ fill: 'rgba(0,0,0,0.05)' }}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Legend iconType="circle" />
                  <Bar dataKey="roi" name="ROI Estimate" fill="#6366f1" radius={[4, 4, 0, 0]} maxBarSize={50} />
                  <Bar dataKey="yield" name="Rental Yield" fill="#10b981" radius={[4, 4, 0, 0]} maxBarSize={50} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            
            <div className="overflow-x-auto mt-6">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-slate-500 uppercase bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-800">
                  <tr>
                    <th className="px-6 py-4 font-medium">Location</th>
                    <th className="px-6 py-4 font-medium">ROI Estimate</th>
                    <th className="px-6 py-4 font-medium">Rental Yield</th>
                    <th className="px-6 py-4 font-medium">Median Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {analytics.map(item => (
                    <tr key={item.location.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                      <td className="px-6 py-4 font-medium text-slate-900 dark:text-white">
                        {item.location.suburb || item.location.city}
                      </td>
                      <td className="px-6 py-4 text-emerald-600 dark:text-emerald-400 font-semibold">
                        {item.roi_estimate || "N/A"}
                      </td>
                      <td className="px-6 py-4">
                        {item.rental_yield || "N/A"}
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        {item.median_price || "N/A"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
