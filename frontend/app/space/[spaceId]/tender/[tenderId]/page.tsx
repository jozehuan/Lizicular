"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { format } from "date-fns"
import { DashboardHeader } from "@/components/dashboard/header"
import { DashboardFooter } from "@/components/dashboard/footer"
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { useApi } from "@/lib/api"
import { AnalysisDisplay } from "@/components/tender/analysis-display"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  FileText,
  TrendingUp,
  AlertTriangle,
  Loader2,
} from "lucide-react"

// Interfaces matching the backend schema
interface TenderDocument {
  filename: string
  content_type: string
}

interface AnalysisResult {
  id: string
  name: string
  procedure_name: string
  created_at: string
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  data: any // Keeping this generic for now, as AnalysisDisplay handles the details
}

interface TenderData {
  id: string
  name: string
  workspace_id: string
  status: string
  created_at: string
  documents: TenderDocument[]
  analysis_results: AnalysisResult[]
}

function getStatusColor(status: string) {
  switch (status) {
    case "draft":
      return "bg-muted text-muted-foreground"
    case "in-progress":
      return "bg-secondary text-secondary-foreground"
    case "analyzed":
      return "bg-accent text-accent-foreground"
    case "completed":
      return "bg-primary text-primary-foreground"
    default:
      return "bg-muted text-muted-foreground"
  }
}

function formatStatus(status: string) {
  return status
    .split("-")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

export default function TenderAnalysisPage({
  params,
}: {
  params: { spaceId: string; tenderId: string }
}) {
  const { spaceId, tenderId } = params
  const [tender, setTender] = useState<TenderData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { getTender } = useApi()

  useEffect(() => {
    const fetchTenderData = async () => {
      try {
        setLoading(true)
        const data = await getTender(tenderId)
        setTender(data)
        setError(null)
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.")
        setTender(null)
      } finally {
        setLoading(false)
      }
    }

    if (tenderId) {
      fetchTenderData()
    }
  }, [tenderId, getTender])

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-16 w-16 animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen text-red-500">
        <AlertTriangle className="h-16 w-16 mb-4" />
        <h1 className="text-2xl font-bold mb-2">Error Fetching Tender</h1>
        <p>{error}</p>
        <Link href="/dashboard">
          <a className="mt-4 text-blue-500 hover:underline">Go to Dashboard</a>
        </Link>
      </div>
    )
  }

  if (!tender) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen">
        <AlertTriangle className="h-16 w-16 mb-4 text-gray-400" />
        <h1 className="text-2xl font-bold mb-2">Tender Not Found</h1>
        <p>The requested tender could not be found.</p>
        <Link href="/dashboard" className="mt-4 text-blue-500 hover:underline">
            Go to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <DashboardHeader />

        <main className="max-w-4xl mx-auto px-6 py-10 flex-1 w-full">
          <Breadcrumb className="mb-8">
            <BreadcrumbList>
              <BreadcrumbItem>
                <BreadcrumbLink
                  href="/dashboard"
                  className="text-muted-foreground hover:text-foreground"
                >
                  Home
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbLink
                  href={`/space/${spaceId}`}
                  className="text-muted-foreground hover:text-foreground"
                >
                  Workspace {spaceId}
                </BreadcrumbLink>
              </BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                <BreadcrumbPage className="text-foreground font-medium">
                  {tender.name}
                </BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>

          <Card className="border-border rounded-xl bg-card mb-8">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-2xl text-foreground">
                    {tender.name}
                  </CardTitle>
                  <p className="text-muted-foreground mt-2">
                    Created {format(new Date(tender.created_at), "MMMM d, yyyy")}
                  </p>
                </div>
                <Badge className={`rounded-lg ${getStatusColor(tender.status)}`}>
                  {formatStatus(tender.status)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">
                    Attached Files
                  </h3>
                  {tender.documents.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No files uploaded
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {tender.documents.map((file) => (
                        <div
                          key={file.filename}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border"
                        >
                          <FileText className="h-4 w-4 text-red-500" />
                          <span className="text-sm text-foreground">
                            {file.filename}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-6 pt-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {tender.analysis_results.length} analysis result
                      {tender.analysis_results.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      {tender.documents.length} file
                      {tender.documents.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-foreground">
              Analysis Results
            </h2>
            <AnalysisDisplay analysisResults={tender.analysis_results} />
          </div>
        </main>

        <DashboardFooter />
        <ChatbotWidget />
      </div>
    </ProtectedRoute>
  )
}
