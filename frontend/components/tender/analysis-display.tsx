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
  canDelete: boolean
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

// Helper component to render a formatted, recursive summary of dynamic analysis data
const DynamicSummary = ({ data }: { data: any }) => {
    const t = useTranslations("AnalysisDisplay");
    const formatKey = (key: string) => key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

    // Main recursive rendering function for each node in the data tree
    const renderSummaryNode = (nodeData: any, nodeKey: string) => {
        // Do not render keys that have null value or are empty arrays
        if (nodeData === null || (Array.isArray(nodeData) && nodeData.length === 0)) {
            return null;
        }

        const formattedKey = formatKey(nodeKey);

        // Case 1: The value is an array -> count its elements
        if (Array.isArray(nodeData)) {
            return <p>{formattedKey}: <span className="font-normal text-muted-foreground">{t('elementsCount', { count: nodeData.length })}</span></p>;
        }

        // Case 2: The value is a nested object -> recurse through its properties
        if (typeof nodeData === 'object' && nodeData !== null) {
            return (
                <div className="mt-2">
                    <p className="font-medium text-foreground">{formattedKey}:</p>
                    <div className="pl-4 border-l-2 border-muted/30 ml-2 space-y-1 mt-1">
                        {Object.entries(nodeData).map(([key, value]) => (
                            <div key={key}>
                                {renderSummaryNode(value, key)}
                            </div>
                        ))}
                    </div>
                </div>
            );
        }

        // Case 3: The value is a primitive (string, number, etc.) -> display it
        return <p>{formattedKey}: <span className="font-normal text-muted-foreground">{String(nodeData)}</span></p>;
    };

    // Filter out all possible metadata keys from the analysis result document
    const metadataKeys = ['_id', 'tender_id', 'created_at', 'id', 'name', 'procedure_id', 'procedure_name', 'created_by', 'processing_time', 'status', 'error_message', 'data'];
    const dataKeysToDisplay = Object.keys(data).filter(
        key => !metadataKeys.includes(key)
    );

    return (
        <div className="space-y-2 text-sm font-semibold text-foreground/90">
            {dataKeysToDisplay.map(key => (
                <div key={key}>
                    {renderSummaryNode(data[key], key)}
                </div>
            ))}
        </div>
    );
};

export function AnalysisDisplay({ analysisResults, onDelete, spaceId, tenderId, canDelete }: AnalysisDisplayProps) {
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
                            {tStatus(normalizedStatus) || normalizedStatus.toUpperCase()}                          </Badge>
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
          
          {canDelete && (
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
          )}
        </div>
      )})}
    </div>
  );
}
