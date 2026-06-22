import NextAuth, { DefaultSession } from "next-auth";
import Google from "next-auth/providers/google";
import Credentials from "next-auth/providers/credentials";
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
    async jwt({ token, user }) {
      if (user) {
        // `user.access_token` is the FastAPI-issued JWT
        // (NextAuth typings don't know about it natively, so we cast to any or just read it)
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
