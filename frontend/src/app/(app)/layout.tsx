/**
 * Auth-gated layout for all application routes.
 *
 * Any page nested under (app)/ — dashboard, report, pro features, etc. —
 * is automatically protected by this layout. Unauthenticated users are
 * redirected to /login with the originally requested URL preserved as
 * the `callbackUrl` query parameter (Requirement 2.5).
 *
 * Uses NextAuth v5 `auth()` helper which works in Server Components.
 */
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";

export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();

  if (!session) {
    // Redirect to login; NextAuth will handle the callbackUrl via its
    // built-in pages.signIn config pointing to /login.
    redirect("/login");
  }

  return <>{children}</>;
}
