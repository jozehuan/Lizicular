"use client"

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle, Clock, FileJson, Loader2, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTranslations } from "next-intl"

// Interfaces based on backend/tenders/schemas.py
interface AnalysisResult {
  id: string
  name: string
  procedure_name: string
  created_at: string
  status: "pending" | "processing" | "completed" | "failed" | string
  data: any | null
  error_message?: string
}

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { getStatusBadgeClasses } from "@/lib/style-utils"
import Link from "next/link"

interface AnalysisDisplayProps {
  analysisResults: AnalysisResult[]
  onDelete: (analysisId: string) => void
  spaceId: string
  tenderId: string
}

const getStatusIcon = (status: AnalysisResult["status"]) => {
  switch (status?.toLowerCase()) {
    case "completed":
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case "processing":
    case "pending":
      return <Loader2 className="h-5 w-5 animate-spin text-blue-800 dark:text-blue-300" />
    case "failed":
      return <AlertCircle className="h-5 w-5 text-destructive" />
    default:
      return <Clock className="h-5 w-5 text-gray-500" />
  }
}

const parseErrorMessage = (message?: string, defaultMessage?: string): string => {
  if (!message) return defaultMessage || "No detail provided.";

  const prefix = "Error from automation service: ";
  let detail = message;

  if (message.startsWith(prefix)) {
    detail = message.substring(prefix.length);
  }

  // Clean up n8n artifacts from the final detail string
  if (detail.startsWith('$input.detail')) {
    detail = detail.substring('$input.detail'.length).trim();
  }
  
  const httpErrorPrefix = "httpx.HTTPStatusError: ";
  if (detail.startsWith(httpErrorPrefix)) {
    detail = detail.substring(httpErrorPrefix.length);
  }

  const urlIndex = detail.indexOf(" for url ");
  if (urlIndex !== -1) {
    detail = detail.substring(0, urlIndex);
  }

  return detail.trim() || defaultMessage || "No detail provided.";
};

// Helper component to render the dynamic summary
const DynamicSummary = ({ data }: { data: any }) => {
    const t = useTranslations("AnalysisDisplay");

    const renderSummary = (obj: any, level = 0) => {
        if (!obj || typeof obj !== 'object') {
        return null;
        }

        const keys = Object.keys(obj).filter(
        k => !['_id', 'tender_id', 'created_at'].includes(k)
        );

        return (
        <ul className={`space-y-1 ${level > 0 ? 'pl-4' : ''}`}>
            {keys.map(key => {
            const value = obj[key];
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

            return (
                <li key={key} className="text-sm">
                <span className="font-semibold">{formattedKey}:</span>
                {Array.isArray(value) ? (
                    <span className="ml-2">{t('elementsCount', { count: value.length })}</span>
                ) : typeof value === 'object' && value !== null ? (
                    renderSummary(value, level + 1)
                ) : (
                    <span className="ml-2">{String(value)}</span>
                )}
                </li>
            );
            })}
        </ul>
        );
    };

    return renderSummary(data);
};

export function AnalysisDisplay({ analysisResults, onDelete, spaceId, tenderId }: AnalysisDisplayProps) {
  const t = useTranslations("AnalysisDisplay");
  const tStatus = useTranslations("Status"); // Add tStatus hook

  if (!analysisResults || analysisResults.length === 0) {
    return (
      <Card className="text-center">
        <CardHeader>
          <FileJson className="mx-auto h-12 w-12 text-gray-400" />
        </CardHeader>
        <CardContent>
          <CardTitle>{t('noAnalysis.title')}</CardTitle>
          <CardDescription>{t('noAnalysis.description')}</CardDescription>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {analysisResults.map((result) => {
        const normalizedStatus = result.status?.toLowerCase() || 'pending';

        return (
        <div key={result.id} className="flex items-start gap-2">
          <Accordion type="single" collapsible className="flex-1">
            <AccordionItem 
              value={result.id} 
              className="border rounded-lg overflow-hidden shadow-sm"
            >
              <AccordionTrigger className="p-4 bg-gray-50 dark:bg-gray-800 hover:no-underline">
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(normalizedStatus)}
                    <div className="text-left">
                      {normalizedStatus === 'completed' ? (
                        <Link 
                          href={`/space/${spaceId}/tender/${tenderId}/${result.id}`}
                          className="font-semibold hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {result.name}
                        </Link>
                      ) : (
                        <p className="font-semibold">{result.name}</p>
                      )}
                      <p className="text-sm text-muted-foreground">
                        {t('created')}: {new Date(result.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pr-2">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Badge
                            variant="outline"
                            className={getStatusBadgeClasses(normalizedStatus)}
                          >
                            {tStatus(normalizedStatus) || result.status.toUpperCase()}
                          </Badge>
                        </TooltipTrigger>
                        {normalizedStatus === 'failed' && (
                          <TooltipContent>
                            <p>{parseErrorMessage(result.error_message, t('noErrorDetails'))}</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
              </AccordionTrigger>
              
              <AccordionContent className="p-4 bg-white dark:bg-black">
                {normalizedStatus === "completed" && result.data ? (
                  <DynamicSummary data={result.data} />
                ) : normalizedStatus === "processing" ? (
                  <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                    <Clock className="h-8 w-8 mb-2 animate-spin" />
                    <p>{t('status.processing')}</p>
                  </div>
                ) : normalizedStatus === "failed" ? (
                  <div className="flex flex-col items-center justify-center p-8 text-destructive">
                    <AlertCircle className="h-8 w-8 mb-2" />
                    <p className="font-semibold">{t('status.failed')}</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                    <Clock className="h-8 w-8 mb-2" />
                    <p>{t('status.pending')}</p>
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
          
          <Button
            variant="ghost"
            size="icon"
            disabled={
              normalizedStatus === 'pending' || 
              normalizedStatus === 'processing'
            }
            onClick={(e) => {
              e.stopPropagation();
              onDelete(result.id);
            }}
            className="shrink-0 text-muted-foreground hover:text-destructive mt-5 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      )})}
    </div>
  );
}
