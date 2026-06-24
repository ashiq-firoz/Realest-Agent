"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

/**
 * Header navigation that reflects auth state:
 *  - signed in  → New Report + Dashboard links + tier chip + Logout
 *  - signed out → Login + Sign up
 */
export function AuthNav() {
  const { data: session, status } = useSession();
  const authed = status === "authenticated";

  const linkClass =
    "hover:text-primary transition-colors flex items-center gap-1 text-on-surface-variant font-label-md text-label-md";

  if (!authed) {
    return (
      <nav className="flex items-center gap-4 text-label-md font-label-md text-on-surface-variant">
        <Link href="/login" className={linkClass}>
          Login
        </Link>
        <Link href="/register">
          <Button size="sm" className="bg-primary-container text-on-primary-container hover:opacity-90 font-label-md rounded-xl">
            Sign up
          </Button>
        </Link>
      </nav>
    );
  }

  const tier = session?.user?.tier;

  return (
    <nav className="flex items-center gap-4 text-label-md font-label-md text-on-surface-variant">
      <Link href="/report/new" className={linkClass}>
        <span className="material-symbols-outlined text-[18px]">search</span>
        <span className="hidden sm:inline">New Report</span>
      </Link>
      <Link href="/dashboard" className={linkClass}>
        <span className="material-symbols-outlined text-[18px]">dashboard</span>
        <span className="hidden sm:inline">Dashboard</span>
      </Link>
      {tier && (
        <span className="hidden sm:inline-flex items-center rounded-full bg-tertiary-container/40 text-on-tertiary-container px-2 py-0.5 text-label-sm font-label-sm capitalize">
          {tier}
        </span>
      )}
      <Button
        variant="outline"
        size="sm"
        onClick={() => signOut({ callbackUrl: "/" })}
        className="flex items-center gap-1 border-outline-variant text-on-surface-variant hover:bg-surface-container-high rounded-xl"
      >
        <span className="material-symbols-outlined text-[18px]">logout</span>
        Logout
      </Button>
    </nav>
  );
}
