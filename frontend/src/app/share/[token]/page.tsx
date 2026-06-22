import { notFound } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { MapPin, Calendar, Share2 } from "lucide-react";
import { apiGet } from "@/lib/api-client";
import { 
  MarketOverview, 
  NeighbourhoodInsights, 
  Demographics, 
  InvestmentIntelligence, 
  ComparableProperties, 
  AISummary 
} from "@/components/report-sections";
import type { ReportResponse } from "@/types/api";

export default async function SharedReportPage({ params }: { params: { token: string } }) {
  let report: ReportResponse | null = null;
  
  try {
    report = await apiGet<ReportResponse>(`/reports/share/${params.token}`);
  } catch (error) {
    console.error("Failed to fetch shared report", error);
  }

  if (!report) {
    notFound();
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-6">
        <div className="space-y-2">
          <Badge variant="outline" className="bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800">
            <Share2 className="w-3 h-3 mr-1 inline-block" /> Shared Report
          </Badge>
          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-3">
            <MapPin className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
            {report.location.display_name}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 font-medium flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Generated on {new Date(report.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <MarketOverview content={report.market_overview} />
        <NeighbourhoodInsights content={report.neighbourhood_insights} />
      </div>

      <Demographics content={report.demographics_section} />

      <InvestmentIntelligence content={report.investment_intelligence} />

      <ComparableProperties properties={report.comparable_properties} />

      <AISummary content={report.ai_summary} />
    </div>
  );
}
