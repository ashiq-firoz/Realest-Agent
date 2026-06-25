"use client";

import React, { useRef, useState } from "react";
import { useSession } from "next-auth/react";
import { Button } from "@/components/ui/button";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export default function DocumentUpload({ chatId, onUploadSuccess }: { chatId: string, onUploadSuccess: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const { data: session } = useSession();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("chat_id", chatId);

    try {
      const res = await fetch(`${BACKEND_URL}/agent/upload`, {
        method: "POST",
        headers: {
          ...(session?.backendToken ? { Authorization: `Bearer ${session.backendToken}` } : {}),
        },
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");
      onUploadSuccess();
    } catch (err) {
      console.error("Failed to upload document", err);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <>
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        className="hidden" 
        accept=".pdf,.doc,.docx,.txt,.md"
      />
      <Button 
        variant="outline" 
        onClick={() => fileInputRef.current?.click()} 
        disabled={isUploading}
        className="flex items-center gap-2"
      >
        <span className="material-symbols-outlined text-sm">{isUploading ? 'sync' : 'upload_file'}</span>
        {isUploading ? 'Uploading...' : 'Upload Doc'}
      </Button>
    </>
  );
}
