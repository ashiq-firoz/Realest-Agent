import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles } from "lucide-react";

interface AISummaryProps {
  content: string;
}

export function AISummary({ content }: AISummaryProps) {
  return (
    <Card className="shadow-lg border-indigo-200/60 dark:border-indigo-800/60 overflow-hidden bg-gradient-to-br from-indigo-50/50 to-white dark:from-indigo-950/20 dark:to-slate-950">
      <CardHeader className="border-b border-indigo-100 dark:border-indigo-900/50 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-indigo-500 text-white rounded-xl shadow-md shadow-indigo-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <CardTitle className="text-xl text-indigo-900 dark:text-indigo-100">AI Summary</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-6 prose dark:prose-invert max-w-none text-slate-700 dark:text-slate-300">
        <ReactMarkdown>{content}</ReactMarkdown>
      </CardContent>
    </Card>
  );
}
