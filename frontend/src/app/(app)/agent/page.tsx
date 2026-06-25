import React from "react";
import ChatInterface from "@/components/agent/chat-interface";

export const metadata = {
  title: "Agent Mode - Novestate",
  description: "Chat with your AI real estate agent.",
};

export default function AgentPage({
  searchParams,
}: {
  searchParams: { q?: string };
}) {
  const initialQuery = searchParams.q || "";

  return (
    <div className="flex-1 flex flex-col bg-background overflow-hidden relative">
      <ChatInterface initialQuery={initialQuery} />
    </div>
  );
}
