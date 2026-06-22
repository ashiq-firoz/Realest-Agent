"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Building2, Loader2, Mail, Lock, User, AlertCircle, Check } from "lucide-react";

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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 via-indigo-50/30 to-slate-100 dark:from-slate-950 dark:via-indigo-950/20 dark:to-slate-950 px-4">
      <div className="absolute top-[-10%] left-[-5%] w-[30%] h-[30%] rounded-full bg-indigo-500/10 blur-[100px] pointer-events-none" />

      <Card className="w-full max-w-md border-slate-200/80 dark:border-slate-800 shadow-2xl shadow-indigo-500/5 backdrop-blur-sm">
        <CardHeader className="text-center space-y-4 pb-2">
          <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Building2 className="w-7 h-7 text-white" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Create your account
            </CardTitle>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Start generating real estate intelligence
            </p>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-4">
          <form onSubmit={handleRegister} className="space-y-4">
            {errors.length > 0 && (
              <div className="space-y-1 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/30 rounded-lg p-3 border border-red-200 dark:border-red-900">
                {errors.map((err, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    {err}
                  </div>
                ))}
              </div>
            )}

            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium text-slate-700 dark:text-slate-300">Name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input id="name" type="text" placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} required className="pl-10 h-11" />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium text-slate-700 dark:text-slate-300">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input id="email" type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required className="pl-10 h-11" />
              </div>
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-slate-700 dark:text-slate-300">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input id="password" type="password" placeholder="Min. 8 characters" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} className="pl-10 h-11" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Choose your mode</label>
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
                      className={`text-left rounded-xl border p-3 transition-all ${
                        active
                          ? "border-indigo-500 ring-2 ring-indigo-500/30 bg-indigo-50 dark:bg-indigo-950/30"
                          : "border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-900 dark:text-white">{opt.title}</span>
                        {active && <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{opt.blurb}</p>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs text-slate-400">No payment required — switch modes anytime.</p>
            </div>

            <Button type="submit" disabled={isLoading} className="w-full h-11 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-all">
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Create account
            </Button>
          </form>

          <p className="text-center text-sm text-slate-500 dark:text-slate-400">
            Already have an account?{" "}
            <Link href="/login" className="text-indigo-600 dark:text-indigo-400 font-medium hover:underline">Sign in</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
