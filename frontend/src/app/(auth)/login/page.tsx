"use client";

import { useState, Suspense } from "react";
import { signIn } from "next-auth/react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";

function LoginContent() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/dashboard";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleCredentialLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl,
      });

      if (result?.error) {
        setError("Invalid email or password. Please try again.");
      } else if (result?.url) {
        window.location.href = result.url;
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    signIn("google", { callbackUrl });
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

        {/* Featured Visual Header */}
        <div className="w-full mb-lg relative overflow-hidden rounded-xl h-48 login-card">
          <div
            className="absolute inset-0 bg-cover bg-center"
          // style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuA6ImEpoxksMHsWbzL8Ma-sra_zAJP6rMvn49wAVM7YF5lxdFT5uTp17mUzCafD_9Rtq6oTMwmarjwy7gUg5zJtEf1y7Y-qpLbRt1V6v41X72NjdX3cDb7mDFxnt8t9sRNGQrz_6ldgnaAeTL1moxPlugsqHCPj88wp7Mcw3GQme5gmPQYX27dPyVejGvkCEe6rnuuCHcfd6Ntnnilp4N1bjAIJrPBPt15Rm7u1uPnubV-lDnn3N3cxJXBjv1P_ca-S39M8PuURTic')" }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background/80 to-transparent" />
          <div className="absolute bottom-md left-md right-md">
            <h1 className="font-headline-lg-mobile text-headline-lg-mobile font-serif text-on-surface">Welcome back</h1>
            <p className="font-body-md text-body-md text-on-surface-variant">Sign in to Estately AI</p>
          </div>
        </div>

        {/* Login Form Container */}
        <div className="w-full bg-surface-container-low rounded-xl p-lg login-card space-y-lg">
          {/* Google Sign In */}
          <button
            type="button"
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-md py-md px-lg bg-surface-container-lowest border border-outline-variant rounded-xl transition-all active:scale-95 duration-100 hover:bg-surface-container-high group"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="font-label-md text-label-md text-on-surface">Continue with Google</span>
          </button>

          <div className="flex items-center gap-md">
            <div className="h-[1px] flex-1 bg-outline-variant" />
            <span className="font-label-sm text-label-sm text-outline uppercase tracking-widest">or email</span>
            <div className="h-[1px] flex-1 bg-outline-variant" />
          </div>

          {/* Email & Password Fields */}
          <form onSubmit={handleCredentialLogin} className="space-y-md">
            {error && (
              <div className="flex items-center gap-2 text-label-sm font-label-sm text-error bg-error-container/30 rounded-xl p-md border border-error/20">
                <span className="material-symbols-outlined text-[18px]">error</span>
                {error}
              </div>
            )}

            <div className="space-y-xs">
              <label className="font-label-sm text-label-sm text-on-surface-variant ml-xs" htmlFor="email">
                Email Address
              </label>
              <input
                className="w-full bg-surface-container-highest border-none rounded-xl px-lg py-md font-body-md text-body-md placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all outline-none"
                id="email"
                placeholder="name@example.com"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-xs">
              <div className="flex justify-between items-center px-xs">
                <label className="font-label-sm text-label-sm text-on-surface-variant" htmlFor="password">
                  Password
                </label>
                <a className="font-label-sm text-label-sm text-primary hover:underline" href="#">
                  Forgot?
                </a>
              </div>
              <div className="relative">
                <input
                  className="w-full bg-surface-container-highest border-none rounded-xl px-lg py-md font-body-md text-body-md placeholder:text-on-surface-variant/40 focus:ring-2 focus:ring-primary focus:bg-surface-container-lowest transition-all outline-none"
                  id="password"
                  placeholder="••••••••"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                />
                <button
                  className="absolute right-md top-1/2 -translate-y-1/2 text-on-surface-variant/60 hover:text-on-surface"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  <span className="material-symbols-outlined text-[20px]">
                    {showPassword ? "visibility_off" : "visibility"}
                  </span>
                </button>
              </div>
            </div>

            <div className="pt-sm">
              <Button
                type="submit"
                disabled={isLoading}
                className="w-full bg-primary-container text-on-primary-container py-md rounded-xl font-label-md text-label-md font-bold shadow-sm hover:opacity-90 active:scale-95 duration-100 transition-all h-auto"
              >
                {isLoading && (
                  <span className="material-symbols-outlined text-[18px] animate-spin mr-2">progress_activity</span>
                )}
                Sign in
              </Button>
            </div>
          </form>
        </div>

        {/* Footer Link */}
        <p className="mt-xl font-body-md text-body-md text-on-surface-variant">
          Don&apos;t have an account?{" "}
          <Link className="text-primary font-bold hover:underline" href="/register">
            Create one
          </Link>
        </p>

        {/* Aesthetic Note / AI Insight Tag */}
        <div className="mt-xl p-md bg-tertiary-container/20 rounded-xl border-l-2 border-tertiary flex items-start gap-md max-w-[320px]">
          <span className="material-symbols-outlined text-tertiary" style={{ fontVariationSettings: "'FILL' 1" }}>auto_fix_high</span>
          <p className="font-label-sm text-label-sm text-on-tertiary-container leading-relaxed">
            Estately AI uses real-time market data to prioritize the homes that match your lifestyle perfectly.
          </p>
        </div>
      </div>
    </div>
  );
}

/**
 * Login page — email/password credentials + Google OAuth.
 * Requirements: 2.1, 2.4, 2.5, 2.6
 */
export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Loading...</div>}>
      <LoginContent />
    </Suspense>
  );
}
