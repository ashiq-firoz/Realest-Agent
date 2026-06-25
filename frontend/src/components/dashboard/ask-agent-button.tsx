"use client";

import { useRouter } from "next/navigation";

/**
 * "Ask Agent" button for the dashboard header — navigates to the AI agent chat.
 * Optionally forwards a query string as ?q=... (none on the dashboard, so it
 * just opens /agent).
 */
export function AskAgentButton({ query = "" }: { query?: string }) {
  const router = useRouter();

  const handleClick = () => {
    const q = query.trim();
    router.push(q ? `/agent?q=${encodeURIComponent(q)}` : "/agent");
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      className="bg-secondary-container text-on-secondary-container font-label-md text-label-md py-3 px-lg rounded-xl flex items-center justify-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md"
    >
      <span className="material-symbols-outlined text-[18px]">bolt</span>
      Ask Agent
    </button>
  );
}
