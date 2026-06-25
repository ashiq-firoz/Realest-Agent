"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import DocumentUpload from "./document-upload";

// Resolve backend base URL correctly for both server & client contexts
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Message {
  id: string;
  role: "user" | "model" | "system";
  content: string;
}

export default function ChatInterface({ initialQuery }: { initialQuery?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatId, setChatId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const { data: session } = useSession();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/agent/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(session?.backendToken ? { Authorization: `Bearer ${session.backendToken}` } : {}),
        },
        body: JSON.stringify({ message: text, chat_id: chatId }),
      });

      if (!res.ok) throw new Error("Failed to send message");

      const data = await res.json();
      if (data.chat_id) setChatId(data.chat_id);

      const modelMsg: Message = { id: Date.now().toString() + 1, role: "model", content: data.response };
      setMessages(prev => [...prev, modelMsg]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { id: Date.now().toString(), role: "system", content: "Error communicating with agent." }]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery && messages.length === 0 && !isLoading) {
      handleSend(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const handleGenerateReport = async (type: string) => {
    if (!chatId) return;
    setIsLoading(true);
    setMessages(prev => [...prev, { id: Date.now().toString(), role: "user", content: `Generate a ${type} Report.` }]);

    try {
      const res = await fetch(`${BACKEND_URL}/agent/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(session?.backendToken ? { Authorization: `Bearer ${session.backendToken}` } : {}),
        },
        body: JSON.stringify({ chat_id: chatId, report_type: type }),
      });

      if (!res.ok) throw new Error("Failed to generate report");

      const data = await res.json();
      const modelMsg: Message = { id: Date.now().toString() + 1, role: "model", content: data.report_content };
      setMessages(prev => [...prev, modelMsg]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto p-4 gap-4">
      <div className="flex justify-between items-center bg-surface-container p-4 rounded-xl shadow-sm border border-outline-variant">
        <div>
          <h2 className="text-title-lg font-title-lg text-on-surface">Agent Mode</h2>
          <p className="text-label-sm text-on-surface-variant">Your AI real estate expert</p>
        </div>
        <div className="flex gap-2">
          {chatId && <DocumentUpload chatId={chatId} onUploadSuccess={() => setMessages(prev => [...prev, { id: Date.now().toString(), role: "system", content: "Document uploaded successfully. I can now reference it." }])} />}
          <Button variant="outline" onClick={() => handleGenerateReport("Comprehensive Analysis")} disabled={!chatId || isLoading}>Generate Report</Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-surface rounded-xl border border-outline-variant p-4 flex flex-col gap-4 shadow-inner">
        {messages.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-on-surface-variant">
            Ask me anything about properties, suburbs, or agents.
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl ${msg.role === 'user' ? 'bg-primary text-on-primary rounded-tr-sm' : msg.role === 'system' ? 'bg-error-container text-on-error-container' : 'bg-surface-container border border-outline-variant rounded-tl-sm prose dark:prose-invert'}`}>
              {msg.role === 'model' ? <ReactMarkdown>{msg.content}</ReactMarkdown> : msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-surface-container border border-outline-variant p-4 rounded-2xl rounded-tl-sm text-on-surface-variant animate-pulse flex items-center gap-2">
              <span className="material-symbols-outlined animate-spin">sync</span>
              Agent is thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="bg-surface-container rounded-xl p-2 border border-outline-variant flex items-center gap-2 shadow-sm">
        <input
          type="text"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend(input)}
          className="flex-1 bg-transparent px-4 py-2 focus:outline-none text-on-surface"
          disabled={isLoading}
        />
        <Button onClick={() => handleSend(input)} disabled={!input.trim() || isLoading} className="rounded-lg">
          <span className="material-symbols-outlined">send</span>
        </Button>
      </div>
    </div>
  );
}
