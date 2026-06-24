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
        callbackUrl: "/dashboard",
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

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-container-margin overflow-x-hidden">
      <div className="grain-overlay" />

      <div className="w-full max-w-md mx-auto py-xl flex flex-col items-center">
        {/* Logo Area */}
        <div className="mb-xl text-center space-y-sm">
          <div className="flex items-center justify-center gap-xs text-primary">
            <span className="material-symbols-outlined text-headline-md" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
            <span className="font-headline-md text-headline-md font-bold font-serif tracking-tight">Estately AI</span>
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
