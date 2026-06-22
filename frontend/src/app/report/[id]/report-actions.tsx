"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Share2, Download, Trash2, Loader2, AlertCircle, Bookmark, Activity } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiDelete, apiPost } from "@/lib/api-client";
import { useSession } from "next-auth/react";

interface ReportActionsProps {
  reportId: string;
  shareToken: string;
  isOwner: boolean;
  locationId: string;
}

export function ReportActions({ reportId, shareToken, isOwner, locationId }: ReportActionsProps) {
  const router = useRouter();
  const { data: session } = useSession();
  const [isDeleting, setIsDeleting] = useState(false);
  const [isSavingLocation, setIsSavingLocation] = useState(false);
  const [isAddingWatchlist, setIsAddingWatchlist] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleShare = async () => {
    try {
      const shareUrl = `${window.location.origin}/share/${shareToken}`;
      await navigator.clipboard.writeText(shareUrl);
      setMessage({ type: 'success', text: 'Link copied!' });
      setTimeout(() => setMessage(null), 3000);
    } catch {
      setMessage({ type: 'error', text: 'Failed to copy link' });
    }
  };

  const handleExport = () => {
    setMessage({ type: 'success', text: 'Opening print dialog — choose "Save as PDF".' });
    setTimeout(() => setMessage(null), 4000);
    window.print();
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    setIsDeleting(true);
    try {
      await apiDelete(`/reports/${reportId}`, session);
      router.push("/dashboard");
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete report' });
      setIsDeleting(false);
    }
  };

  const handleSaveLocation = async () => {
    setIsSavingLocation(true);
    try {
      await apiPost("/dashboard/saved-locations", { location_id: locationId }, session);
      setMessage({ type: 'success', text: 'Location saved!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to save location' });
    } finally {
      setIsSavingLocation(false);
    }
  };

  const handleAddWatchlist = async () => {
    setIsAddingWatchlist(true);
    try {
      await apiPost("/watchlist", { location_id: locationId }, session);
      setMessage({ type: 'success', text: 'Added to watchlist!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || 'Failed to add to watchlist' });
    } finally {
      setIsAddingWatchlist(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-2 no-print">
      <div className="flex items-center gap-2 flex-wrap justify-end">
        {session?.backendToken && (
          <>
            <Button variant="outline" onClick={handleSaveLocation} disabled={isSavingLocation} className="gap-2">
              {isSavingLocation ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bookmark className="w-4 h-4" />}
              Save Location
            </Button>
            <Button variant="outline" onClick={handleAddWatchlist} disabled={isAddingWatchlist} className="gap-2">
              {isAddingWatchlist ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
              Watchlist
            </Button>
          </>
        )}
        <Button variant="outline" onClick={handleShare} className="gap-2">
          <Share2 className="w-4 h-4" />
          Share
        </Button>
        {isOwner && (
          <>
            <Button variant="outline" onClick={handleExport} className="gap-2">
              <Download className="w-4 h-4" />
              Export PDF
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={isDeleting} className="gap-2">
              {isDeleting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
              Delete
            </Button>
          </>
        )}
      </div>
      {message && (
        <div className={`text-sm flex items-center gap-1 ${message.type === 'error' ? 'text-red-500' : 'text-emerald-500'}`}>
          {message.type === 'error' && <AlertCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}
    </div>
  );
}
