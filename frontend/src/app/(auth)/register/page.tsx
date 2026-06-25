"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

/**
 * Register page — creates account via FastAPI, then signs in.
 * Requirements: 2.1, 2.2, 2.3, 2.6
 */
export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tier, setTier] = useState<"regular" | "pro">("regular");
  const [errors, setErrors] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Where to land after signup. Preserves any ?callbackUrl=... (e.g. an /agent?q=...
  // target forwarded from the home "Ask Agent" flow), defaulting to the dashboard.
  const getCallbackUrl = () =>
    (typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).get("callbackUrl")) ||
    "/dashboard";

  const validate = (): string[] => {
    const errs: string[] = [];
    if (!email.includes("@") || !email.includes(".")) {
      errs.push("Please enter a valid email address.");
    }
    if (password.length < 8) {
      errs.push("Password must be at least 8 characters.");
    }
    return errs;
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors([]);
    setIsLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password, tier }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setErrors([body?.detail ?? `Registration failed (HTTP ${res.status})`]);
        return;
      }

      // Auto sign-in after successful registration
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl: getCallbackUrl(),
      });

      if (result?.url) {
        window.location.href = result.url;
      } else {
        router.push("/login");
      }
    } catch {
      setErrors(["Network error — please check your connection."]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignup = () => {
    // Persist the chosen mode across the Google OAuth redirect so the backend
    // creates the new account with the selected tier (read in the NextAuth callback).
    document.cookie = `signup_tier=${tier}; path=/; max-age=600; samesite=lax`;
    signIn("google", { callbackUrl: getCallbackUrl() });
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-container-margin overflow-x-hidden">
      <div className="grain-overlay" />

      <div className="w-full max-w-md mx-auto py-xl flex flex-col items-center">
        {/* Logo Area */}
        <div className="mb-xl text-center space-y-sm">
          <div className="flex items-center justify-center gap-xs text-primary">
            <span className="material-symbols-outlined text-headline-md" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
            <span className="font-headline-md text-headline-md font-bold font-serif tracking-tight">Novestate</span>
          </div>
        </div>

        {/* Visual Header */}
        <div className="w-full mb-lg relative overflow-hidden rounded-xl h-40 login-card">
          <div
            className="absolute inset-0 bg-cover bg-center"
          // style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuA6ImEpoxksMHsWbzL8Ma-sra_zAJP6rMvn49wAVM7YF5lxdFT5uTp17mUzCafD_9Rtq6oTMwmarjwy7gUg5zJtEf1y7Y-qpLbRt1V6v41X72NjdX3cDb7mDFxnt8t9sRNGQrz_6ldgnaAeTL1moxPlugsqHCPj88wp7Mcw3GQme5gmPQYX27dPyVejGvkCEe6rnuuCHcfd6Ntnnilp4N1bjAIJrPBPt15Rm7u1uPnubV-lDnn3N3cxJXBjv1P_ca-S39M8PuURTic')" }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
          <div className="absolute bottom-md left-md right-md">
            <h1 className="font-headline-lg-mobile text-headline-lg-mobile font-serif text-on-surface">Create your account</h1>
            <p className="font-body-md text-body-md text-on-surface-variant">Start generating real estate intelligence</p>
          </div>
        </div>

        {/* Register Form Container */}
        <div className="w-full bg-surface-container-low rounded-xl p-lg login-card space-y-lg">
          <form onSubmit={handleRegister} className="space-y-md">
            {errors.length > 0 && (
              <div className="space-y-1 text-label-sm font-label-sm text-error bg-error-container/30 rounded-xl p-md border border-error/20">
                {errors.map((err, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">error</span>
                    {err}
                  </div>
                ))}
              </div>
            )}

            <div className="space-y-xs">
              <label className="font-label-sm text-label-sm text-on-surface-variant ml-xs" htmlFor="name">Name</label>
              <input
                className="w-full bg-surface-container-highest border-none rounded-xl px-lg py-md font-body-md text-body-md placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all outline-none"
                id="name" type="text" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} required
              />
            </div>

            <div className="space-y-xs">
              <label className="font-label-sm text-label-sm text-on-surface-variant ml-xs" htmlFor="email">Email</label>
              <input
                className="w-full bg-surface-container-highest border-none rounded-xl px-lg py-md font-body-md text-body-md placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all outline-none"
                id="email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required
              />
            </div>

            <div className="space-y-xs">
              <label className="font-label-sm text-label-sm text-on-surface-variant ml-xs" htmlFor="password">Password</label>
              <input
                className="w-full bg-surface-container-highest border-none rounded-xl px-lg py-md font-body-md text-body-md placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all outline-none"
                id="password" type="password" placeholder="Min. 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}
              />
            </div>

            <div className="space-y-xs">
              <label className="font-label-sm text-label-sm text-on-surface-variant ml-xs">Choose your mode</label>
              <div className="grid grid-cols-2 gap-3">
                {([
                  { id: "regular", title: "Regular", blurb: "Reports, dashboard & exports" },
                  { id: "pro", title: "Pro", blurb: "Watchlist, saved locations & analytics" },
                ] as const).map((opt) => {
                  const active = tier === opt.id;
                  return (
                    <button
                      type="button"
                      key={opt.id}
                      onClick={() => setTier(opt.id)}
                      aria-pressed={active}
                      className={`text-left rounded-xl border p-3 transition-all ${active
                        ? "border-primary ring-2 ring-primary/30 bg-primary-container/20"
                        : "border-outline-variant hover:border-outline"
                        }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-label-md text-label-md text-on-surface">{opt.title}</span>
                        {active && <span className="material-symbols-outlined text-[18px] text-primary">check</span>}
                      </div>
                      <p className="text-label-sm font-label-sm text-on-surface-variant mt-1">{opt.blurb}</p>
                    </button>
                  );
                })}
              </div>
              <p className="text-label-sm font-label-sm text-on-surface-variant/60 ml-xs">No payment required — switch modes anytime.</p>
            </div>

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-primary-container text-on-primary-container py-md rounded-xl font-label-md text-label-md font-bold shadow-sm hover:opacity-90 active:scale-95 duration-100 transition-all h-auto"
            >
              {isLoading && <span className="material-symbols-outlined text-[18px] animate-spin mr-2">progress_activity</span>}
              Create account
            </Button>
          </form>

          <div className="flex items-center gap-md">
            <div className="h-[1px] flex-1 bg-outline-variant" />
            <span className="font-label-sm text-label-sm text-outline uppercase tracking-widest">or</span>
            <div className="h-[1px] flex-1 bg-outline-variant" />
          </div>

          {/* Google Sign Up — uses the mode selected above */}
          <button
            type="button"
            onClick={handleGoogleSignup}
            className="w-full flex items-center justify-center gap-md py-md px-lg bg-surface-container-lowest border border-outline-variant rounded-xl transition-all active:scale-95 duration-100 hover:bg-surface-container-high"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="font-label-md text-label-md text-on-surface">Sign up with Google as {tier === "pro" ? "Pro" : "Regular"}</span>
          </button>
        </div>

        {/* Footer Link */}
        <p className="mt-xl font-body-md text-body-md text-on-surface-variant">
          Already have an account?{" "}
          <Link href="/login" className="text-primary font-bold hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
