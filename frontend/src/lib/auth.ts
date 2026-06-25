import NextAuth, { DefaultSession } from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
import { cookies } from "next/headers";
import "next-auth/jwt";

// ---------------------------------------------------------------------------
// TypeScript module augmentation — extends NextAuth built-in types so that
// `session.backendToken` and `session.user.tier` are available everywhere.
// ---------------------------------------------------------------------------
declare module "next-auth" {
  interface Session {
    backendToken?: string;
    user: {
      tier?: string;
    } & DefaultSession["user"];
  }

  interface User {
    token?: string;
    tier?: string;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    backendToken?: string;
    tier?: string;
  }
}

// ---------------------------------------------------------------------------
// NextAuth v5 configuration
// ---------------------------------------------------------------------------
export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    // ------------------------------------------------------------------
    // Google OAuth
    // ------------------------------------------------------------------
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),

    // ------------------------------------------------------------------
    // Email + password — delegates to the FastAPI backend for validation
    // and JWT issuance. The backend returns { id, email, name, tier, token }.
    // ------------------------------------------------------------------
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        try {
          const backendUrl =
            process.env.BACKEND_URL ?? "http://localhost:8000";

          const res = await fetch(`${backendUrl}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (!res.ok) {
            return null;
          }

          // Expected shape: { id, email, name, tier, token }
          const user = await res.json();
          return user ?? null;
        } catch {
          // Network error or backend unavailable
          return null;
        }
      },
    }),
  ],

  callbacks: {
    // ------------------------------------------------------------------
    // jwt — called when a token is created or updated.
    // On first sign-in `user` is populated; on subsequent calls it is
    // undefined, so we carry forward the stored values.
    // ------------------------------------------------------------------
    async jwt({ token, user, account }) {
      // Google sign-in/up: exchange the Google access token for a backend JWT.
      // The chosen tier (set as a cookie on the register page before redirect) is
      // applied only when the backend creates a brand-new user.
      if (account?.provider === "google" && (account as any).access_token) {
        try {
          const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
          let tier = "regular";
          try {
            const c = (await cookies()).get("signup_tier")?.value;
            if (c === "pro" || c === "regular") tier = c;
          } catch {
            /* cookies() unavailable outside a request scope — ignore */
          }
          const res = await fetch(`${backendUrl}/auth/google`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ access_token: (account as any).access_token, tier }),
          });
          if (res.ok) {
            const data = await res.json(); // { access_token, tier }
            token.backendToken = data.access_token;
            token.tier = data.tier;
          }
        } catch {
          /* network error — leave token without backendToken */
        }
      } else if (user) {
        // Credentials sign-in: the backend JWT + tier come back on the user object.
        token.backendToken = (user as any).access_token || user.token;
        token.tier = user.tier;
        token.id = user.id;
      }
      return token;
    },

    // ------------------------------------------------------------------
    // session — called when a session is read by the app.
    // Exposes backendToken and user.tier on the client-side session object.
    // ------------------------------------------------------------------
    async session({ session, token }) {
      session.backendToken = token.backendToken;
      session.user.tier = token.tier;
      return session;
    },
  },

  pages: {
    signIn: "/login",
  },

  secret: process.env.NEXTAUTH_SECRET,
});
