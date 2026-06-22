import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, MapPin, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiGet } from "@/lib/api-client";
import { auth } from "@/lib/auth";
import type { DashboardReport } from "@/types/api";
import { SavedLocations } from "@/components/dashboard/saved-locations";
import { WatchlistPanel } from "@/components/dashboard/watchlist-panel";
import { InvestmentAnalytics } from "@/components/dashboard/investment-analytics";
import { DeleteReportButton } from "@/components/dashboard/delete-report-button";

export default async function DashboardPage() {
  const session = await auth();
  let reports: DashboardReport[] = [];

  try {
    reports = await apiGet<DashboardReport[]>("/dashboard/reports", session);
  } catch (error) {
    console.error("Failed to fetch reports", error);
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            My Dashboard
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            View your recently generated real estate intelligence reports.
          </p>
        </div>
        <Link href="/">
          <Button className="bg-indigo-600 hover:bg-indigo-700 text-white flex items-center gap-2">
            <Search className="w-4 h-4" />
            New Analysis
          </Button>
        </Link>
      </div>

      {reports.length === 0 ? (
        <div className="text-center py-20 bg-slate-50 dark:bg-slate-900/50 rounded-2xl border border-slate-200 dark:border-slate-800 border-dashed">
          <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <MapPin className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">No reports yet</h2>
          <p className="text-slate-500 mt-2 max-w-md mx-auto">
            Generate your first AI-powered real estate market report to see it here.
          </p>
          <Link href="/" className="inline-block mt-6">
            <Button variant="outline" className="border-indigo-200 text-indigo-700 hover:bg-indigo-50 dark:border-indigo-800/60 dark:text-indigo-400 dark:hover:bg-indigo-900/20">
              Start Analyzing
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map((report) => (
            <Card key={report.id} className="shadow-md hover:shadow-lg transition-shadow border-slate-200/60 dark:border-slate-800/60 flex flex-col">
              <CardHeader className="pb-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50">
                <CardTitle className="text-lg flex items-start justify-between gap-4">
                  <span className="line-clamp-2">{report.location.display_name}</span>
                  <Badge variant="secondary" className="shrink-0 bg-white dark:bg-slate-800">
                    {new Date(report.created_at).toLocaleDateString()}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4 flex-1 flex flex-col justify-end">
                <div className="flex items-center gap-2 w-full">
                  <Link href={`/report/${report.id}`} className="flex-1">
                    <Button variant="outline" className="w-full justify-between hover:bg-slate-50 dark:hover:bg-slate-800">
                      View Full Report
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                  <DeleteReportButton reportId={report.id} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pro Dashboard Panels */}
      {/* <div className="pt-8 mt-12 border-t border-slate-200 dark:border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mb-6">
          Pro Intelligence Features
        </h2>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
          <div className="col-span-1">
            <SavedLocations />
          </div>
          <div className="col-span-1 xl:col-span-2 space-y-8">
            <WatchlistPanel />
            <InvestmentAnalytics />
          </div>
        </div>
      </div> */}
      <div className="pt-8 mt-12 border-t border-slate-200 dark:border-slate-800">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white mb-6">
          Pro Intelligence Features
        </h2>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

          {/* Left Column */}
          <div className="col-span-1 space-y-8">
            <SavedLocations />
            <WatchlistPanel />
          </div>

          {/* Right Column */}
          <div className="col-span-1 xl:col-span-2">
            <InvestmentAnalytics />
          </div>

        </div>
      </div>
    </div>
  );
}
