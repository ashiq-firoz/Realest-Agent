"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Trash2, Loader2 } from "lucide-react";
import { apiDelete } from "@/lib/api-client";
import { useSession } from "next-auth/react";

export function DeleteReportButton({ reportId }: { reportId: string }) {
  const router = useRouter();
  const { data: session } = useSession();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    setIsDeleting(true);
    try {
      await apiDelete(`/reports/${reportId}`, session);
      router.refresh();
    } catch (error) {
      console.error(error);
      setIsDeleting(false);
    }
  };

  return (
    <Button 
      variant="outline" 
      onClick={handleDelete}
      disabled={isDeleting}
      className="shrink-0 text-red-500 hover:text-red-600 hover:bg-red-50 border-red-100 dark:border-red-900/30 px-3"
      title="Delete Report"
    >
      {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
    </Button>
  );
}
