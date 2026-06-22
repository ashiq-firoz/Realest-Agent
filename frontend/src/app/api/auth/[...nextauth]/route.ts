/**
 * NextAuth v5 route handler.
 *
 * The `handlers` export from our auth config contains named `GET` and
 * `POST` handlers that NextAuth uses for OAuth callbacks, credentials
 * sign-in, CSRF checks, and session reads.
 *
 * This file must be placed at:
 *   app/api/auth/[...nextauth]/route.ts
 *
 * @see https://authjs.dev/getting-started/installation?framework=Next.js
 */
import { handlers } from "@/lib/auth";

export const GET = handlers.GET;
export const POST = handlers.POST;
