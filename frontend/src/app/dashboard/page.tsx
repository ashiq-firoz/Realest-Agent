import Link from "next/link";
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
    <div className="max-w-5xl mx-auto w-full px-container-margin py-lg space-y-xl animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Dashboard Header */}
      <section className="flex flex-col md:flex-row justify-between gap-md border-b border-outline-variant pb-lg">
        <div>
          <h1 className="text-headline-lg font-headline-lg font-serif text-on-surface">
            My Dashboard
          </h1>
          <p className="text-body-md font-body-md text-on-surface-variant mt-xs">
            View your recently generated real estate intelligence reports.
          </p>
        </div>
        <Link href="/report/new">
          <button className="bg-primary text-on-primary font-label-md text-label-md py-3 px-lg rounded-xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md">
            <span className="material-symbols-outlined text-[18px]">search</span>
            New Analysis
          </button>
        </Link>
      </section>

      {/* Featured Assets */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-md">
        <div className="relative group overflow-hidden rounded-xl h-48 card-shadow bg-surface-container">
          <img
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBBQ3GLKB5DT97VnsQ9PVRVFS_fM6oTF41VoCVHgZIXJw0aLTnZMOIwecjuOgu2E78ix2ZCAkj67fn2ujaPTB3GPxCsNqeNiyFwVRECBK9_dsHoUOOTOY2yS1MTb5d-wD__V2DLED9MY7FxneR4HEhsEVQCw2Z6j5TeFdRXKG9hDUy8xNwyLI8eIHKI4rcn_tmyNSLh58_6nzwiKFTsrGCLFgAUsjE6LwKoq_37RqJoWap9AkSuxb99R2i6DctUrwmz_2yjD-6zyz8"
            alt="Market Volatility Index"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <div className="absolute bottom-4 left-4 text-white">
            <span className="font-label-sm text-label-sm uppercase tracking-wider opacity-80">Latest Analysis</span>
            <h3 className="font-headline-md text-headline-md font-serif leading-tight">Market Volatility Index</h3>
          </div>
        </div>
        <div className="relative group overflow-hidden rounded-xl h-48 card-shadow bg-surface-container">
          <img
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBJys1ZTjrUmbboGXH9O5Wr3KiH6sc7SlpRUExvehXxuYk0UA2TRexsfNeMXUrkKAslijkR5ELTX8svzgTyUuaQPgdXZQ6icHm_2lPqhPeXohN6pvXsSr5dUKpGdkK-JmazINL6afQemSwsyCNccuhvLt_G9zKOnxHYkKla1TUfctcNgipZp2L5KuaC9oBKPL77PssTMNLXyQ9mQ9EufqWgkj6IYJKWHHYzvhXL2dtDau8s9xScmBjPVNM7PHcj3uZL-s0_2kF_xY4"
            alt="Yield Projections Q4"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <div className="absolute bottom-4 left-4 text-white">
            <span className="font-label-sm text-label-sm uppercase tracking-wider opacity-80">Portfolio Review</span>
            <h3 className="font-headline-md text-headline-md font-serif leading-tight">Yield Projections Q4</h3>
          </div>
        </div>
      </section>

      {/* AI Top Picks */}
      <section>
        <div className="flex justify-between items-end mb-md">
          <h3 className="text-headline-md font-headline-md font-serif text-on-surface">AI Top Picks</h3>
          <Link href="/report/new" className="font-label-md text-label-md text-primary hover:opacity-80 transition-opacity">
            Explore All
          </Link>
        </div>
        <div className="space-y-md">
          {/* AI Insight Card 1 */}
          <div className="ai-accent-border bg-surface-container-low p-md rounded-r-xl card-shadow">
            <div className="flex items-center gap-2 mb-sm">
              <span className="material-symbols-outlined text-[18px] text-secondary" style={{ fontVariationSettings: "'FILL' 1" }}>bolt</span>
              <span className="font-label-md text-label-md text-secondary">High Potential</span>
            </div>
            <h4 className="text-headline-md font-headline-md font-serif mb-2">Sandy Bay Terraces</h4>
            <p className="text-body-md font-body-md text-on-surface-variant mb-md">
              AI signals 8.2% growth in TAS coastal properties. Strong rental demand from luxury tourism sector.
            </p>
            <div className="space-y-3">
              <div className="flex flex-col gap-1">
                <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant uppercase">
                  <span>ROI Estimate</span>
                  <span>12.4%</span>
                </div>
                <div className="h-1.5 w-full bg-outline-variant rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: "82%" }} />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant uppercase">
                  <span>Rental Yield</span>
                  <span>5.1%</span>
                </div>
                <div className="h-1.5 w-full bg-outline-variant rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary rounded-full" style={{ width: "45%" }} />
                </div>
              </div>
            </div>
          </div>
          {/* AI Insight Card 2 */}
          <div className="ai-accent-border bg-surface-container-low p-md rounded-r-xl card-shadow opacity-90">
            <div className="flex items-center gap-2 mb-sm">
              <span className="material-symbols-outlined text-[18px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>insights</span>
              <span className="font-label-md text-label-md text-primary">Stable Core</span>
            </div>
            <h4 className="text-headline-md font-headline-md font-serif mb-2">Richmond Lofts</h4>
            <p className="text-body-md font-body-md text-on-surface-variant mb-md">
              Consistently low vacancy rates. Ideal for long-term equity building with 4% annual growth.
            </p>
            <div className="space-y-3">
              <div className="flex flex-col gap-1">
                <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant uppercase">
                  <span>ROI Estimate</span>
                  <span>7.8%</span>
                </div>
                <div className="h-1.5 w-full bg-outline-variant rounded-full overflow-hidden">
                  <div className="h-full bg-primary rounded-full" style={{ width: "60%" }} />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant uppercase">
                  <span>Rental Yield</span>
                  <span>4.2%</span>
                </div>
                <div className="h-1.5 w-full bg-outline-variant rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary rounded-full" style={{ width: "38%" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Saved Reports Section */}
      <section>
        <h3 className="text-headline-md font-headline-md font-serif text-on-surface mb-md">Saved Reports</h3>
        {reports.length === 0 ? (
          <div className="text-center py-16 tonal-card rounded-2xl border-dashed">
            <div className="w-16 h-16 bg-primary-container/30 text-primary rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="material-symbols-outlined text-4xl">location_on</span>
            </div>
            <h4 className="text-headline-md font-headline-md font-serif text-on-surface">No reports yet</h4>
            <p className="text-body-md font-body-md text-on-surface-variant mt-2 max-w-md mx-auto">
              Generate your first AI-powered real estate market report to see it here.
            </p>
            <Link href="/report/new" className="inline-block mt-6">
              <button className="bg-primary-container text-on-primary-container font-label-md text-label-md py-3 px-lg rounded-xl hover:opacity-90 active:scale-95 transition-all">
                Start Analyzing
              </button>
            </Link>
          </div>
        ) : (
          <div className="flex overflow-x-auto gap-md scroll-hide pb-2">
            {reports.map((report) => (
              <div
                key={report.id}
                className="flex-none w-56 bg-surface-container-high rounded-xl p-md card-shadow border border-outline-variant"
              >
                <div className="w-full h-24 mb-md rounded-lg overflow-hidden bg-white/50">
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="material-symbols-outlined text-primary text-4xl opacity-40">description</span>
                  </div>
                </div>
                <h5 className="font-label-md text-label-md text-on-surface mb-0.5 line-clamp-2">
                  {report.location.display_name}
                </h5>
                <p className="font-label-sm text-label-sm text-on-surface-variant mb-3">
                  {new Date(report.created_at).toLocaleDateString()}
                </p>
                <div className="flex items-center gap-2">
                  <Link href={`/report/${report.id}`} className="flex-1">
                    <button className="w-full text-label-sm font-label-sm bg-primary-container/50 text-on-primary-container py-2 rounded-lg hover:bg-primary-container transition-colors flex items-center justify-center gap-1">
                      View
                      <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
                    </button>
                  </Link>
                  <DeleteReportButton reportId={report.id} />
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Pro Intelligence Features */}
      <div className="pt-lg mt-lg border-t border-outline-variant">
        <h2 className="text-headline-md font-headline-md font-serif text-on-surface mb-lg">
          Pro Intelligence Features
        </h2>
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-lg">
          <div className="col-span-1 space-y-lg">
            <SavedLocations />
            <WatchlistPanel />
          </div>
          <div className="col-span-1 xl:col-span-2">
            <InvestmentAnalytics />
          </div>
        </div>
      </div>
    </div>
  );
}
