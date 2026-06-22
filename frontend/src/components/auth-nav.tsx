"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Search, LogOut } from "lucide-react";

/**
 * Header navigation that reflects auth state:
 *  - signed in  → New Report + Dashboard links + tier chip + Logout
 *  - signed out → Login + Sign up
 */
export function AuthNav() {
  const { data: session, status } = useSession();
  const authed = status === "authenticated";

  const linkClass =
    "hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex items-center gap-1";

  if (!authed) {
    return (
      <nav className="flex items-center gap-4 text-sm font-medium text-slate-600 dark:text-slate-300">
        <Link href="/login" className={linkClass}>
          Login
        </Link>
        <Link href="/register">
          <Button size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white">
            Sign up
          </Button>
        </Link>
      </nav>
    );
  }

  const tier = session?.user?.tier;

  return (
    <nav className="flex items-center gap-4 text-sm font-medium text-slate-600 dark:text-slate-300">
      <Link href="/report/new" className={linkClass}>
        <Search className="w-4 h-4" />
        <span className="hidden sm:inline">New Report</span>
      </Link>
      <Link href="/dashboard" className={linkClass}>
        <LayoutDashboard className="w-4 h-4" />
        <span className="hidden sm:inline">Dashboard</span>
      </Link>
      {tier && (
        <span className="hidden sm:inline-flex items-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 px-2 py-0.5 text-xs font-semibold capitalize">
          {tier}
        </span>
      )}
      <Button
        variant="outline"
        size="sm"
        onClick={() => signOut({ callbackUrl: "/" })}
        className="flex items-center gap-1 border-slate-200 dark:border-slate-700"
      >
        <LogOut className="w-4 h-4" />
        Logout
      </Button>
    </nav>
  );
}
