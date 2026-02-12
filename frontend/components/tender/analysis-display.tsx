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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle, Clock, FileJson, Info, Loader2, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"

// Interfaces based on backend/tenders/schemas.py
interface InformacionGeneral {
  requisito: string
  detalle: string
  referencia: string
}

interface Requisito {
  requisito: string
  detalle: string
  referencia: string
}

interface OtroRequisito {
  requisito: string
  detalle: string
  referencia: string
}

interface Subcriterio {
  nombre: string
  detalle: string
  puntuacion: number
  referencia: string
}

interface CriterioNoMatematico {
  nombre: string
  detalle: string
  puntuacion_total: number
  referencia: string
  subcriterios: Subcriterio[]
}

interface Variable {
  simbolo: string
  detalle: string
}

interface Formula {
  formula: string
  detalle_formula: string
  variables: Variable[]
}

interface CriterioMatematico {
  nombre: string
  detalle: string
  puntuacion: number
  referencia: string
  formula: Formula
}

interface AnalysisData {
  informacion_general: InformacionGeneral[]
  requisitos: Requisito[]
  otros_requisitos: OtroRequisito[]
  criterios_no_matematicos: CriterioNoMatematico[]
  criterios_matematicos: CriterioMatematico[]
}

interface AnalysisResult {
  id: string
  name: string
  procedure_name: string
  created_at: string
  status: "pending" | "processing" | "completed" | "failed" | string
  data: AnalysisData | null
  error_message?: string
}

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
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
      return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
    case "failed":
      return <AlertCircle className="h-5 w-5 text-red-500" />
    default:
      return <Clock className="h-5 w-5 text-blue-500" />
  }
}

const getStatusBadgeClasses = (status: AnalysisResult["status"]) => {
  switch (status?.toLowerCase()) {
    case "completed":
      return "bg-green-100 text-green-800 border-green-200 dark:bg-green-900/40 dark:text-green-300 dark:border-green-800"
    case "processing":
    case "pending":
      return "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/40 dark:text-blue-300 dark:border-blue-800"
    case "failed":
      return "bg-red-100 text-red-800 border-red-200 dark:bg-red-900/40 dark:text-red-300 dark:border-red-800"
    default:
      return "bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/40 dark:text-gray-300 dark:border-gray-800"
  }
}

const parseErrorMessage = (message?: string): string => {
  if (!message) return "No detail provided.";

  const prefix = "Error from automation service: ";
  let detail = message;

  if (message.startsWith(prefix)) {
    detail = message.substring(prefix.length);
  }

  // Clean up n8n artifacts from the final detail string
  if (detail.startsWith('$input.detail')) {
    detail = detail.substring('$input.detail'.length).trim();
  }
  
  // Also handle cases where the error from httpx is the main content
  const httpErrorPrefix = "httpx.HTTPStatusError: ";
  if (detail.startsWith(httpErrorPrefix)) {
    detail = detail.substring(httpErrorPrefix.length);
  }

  // NEW: Remove URL part from the error string
  const urlIndex = detail.indexOf(" for url ");
  if (urlIndex !== -1) {
    detail = detail.substring(0, urlIndex);
  }

  return detail.trim() || "No detail provided.";
};

// Helper component to render the dynamic summary
const DynamicSummary = ({ data }: { data: any }) => {
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
                <span className="ml-2">{value.length} elementos</span>
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
  if (!analysisResults || analysisResults.length === 0) {
    return (
      <Card className="text-center">
        <CardHeader>
          <FileJson className="mx-auto h-12 w-12 text-gray-400" />
        </CardHeader>
        <CardContent>
          <CardTitle>No Analysis Available</CardTitle>
          <CardDescription>
            There are no analysis results to display for this tender yet.
          </CardDescription>
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
              className="border rounded-lg overflow-hidden"
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
                        Created: {new Date(result.created_at).toLocaleString()}
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
                            {result.status.toUpperCase()}
                          </Badge>
                        </TooltipTrigger>
                        {normalizedStatus === 'failed' && (
                          <TooltipContent>
                            <p>{parseErrorMessage(result.error_message)}</p>
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
                    <p>Analysis in progress, please wait...</p>
                  </div>
                ) : normalizedStatus === "failed" ? (
                  <div className="flex flex-col items-center justify-center p-8 text-destructive">
                    <AlertCircle className="h-8 w-8 mb-2" />
                    <p className="font-semibold">Analysis Failed</p>
                    {/* The detailed message is now in the tooltip */}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center p-8 text-muted-foreground">
                    <Clock className="h-8 w-8 mb-2" />
                    <p>Analysis is pending and will start soon.</p>
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
