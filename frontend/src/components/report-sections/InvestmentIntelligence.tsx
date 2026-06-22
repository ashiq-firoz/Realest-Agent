import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign } from "lucide-react";

interface InvestmentIntelligenceProps {
  content: string;
}

export function InvestmentIntelligence({ content }: InvestmentIntelligenceProps) {
  return (
    <Card className="shadow-lg border-slate-200/60 dark:border-slate-800/60 overflow-hidden">
      <CardHeader className="bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-xl">
            <DollarSign className="w-5 h-5" />
          </div>
          <CardTitle className="text-xl">Investment Intelligence</CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-6 prose dark:prose-invert max-w-none text-slate-700 dark:text-slate-300">
        <ReactMarkdown>{content}</ReactMarkdown>
      </CardContent>
    </Card>
  );
}
