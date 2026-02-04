"use client"

import { use } from "react"
import Link from "next/link"
import { format } from "date-fns"
import { DashboardHeader } from "@/components/dashboard/header"
import { DashboardFooter } from "@/components/dashboard/footer"
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget"
import { ProtectedRoute } from "@/components/auth/protected-route"
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
import { FileText, CheckCircle, AlertCircle, Clock, TrendingUp } from "lucide-react"

interface AnalysisResult {
  id: string
  title: string
  summary: string
  date: Date
  status: "success" | "warning" | "info"
  insights: string[]
}

interface TenderData {
  id: string
  title: string
  spaceName: string
  spaceId: string
  status: "draft" | "in-progress" | "analyzed" | "completed"
  createdAt: Date
  files: { name: string; type: string }[]
  analysisResults: AnalysisResult[]
}

const tendersData: Record<string, TenderData> = {
  t1: {
    id: "t1",
    title: "Highway Construction Tender 2024",
    spaceName: "Government Infrastructure Projects",
    spaceId: "1",
    status: "analyzed",
    createdAt: new Date("2024-01-20"),
    files: [
      { name: "Technical_Requirements.pdf", type: "pdf" },
      { name: "Budget_Proposal.pdf", type: "pdf" },
    ],
    analysisResults: [
      {
        id: "ar1",
        title: "Budget Analysis Complete",
        summary:
          "The proposed budget of $4.5M is within the expected range for projects of this scope. Cost breakdown shows 60% allocated to materials, 30% to labor, and 10% to contingency.",
        date: new Date("2024-02-15T14:30:00"),
        status: "success",
        insights: [
          "Budget is competitive compared to similar projects",
          "Contingency fund is adequate",
          "Labor costs are below market average",
        ],
      },
      {
        id: "ar2",
        title: "Technical Requirements Review",
        summary:
          "All technical specifications meet industry standards. Some requirements may benefit from clarification regarding material grades and testing protocols.",
        date: new Date("2024-02-10T09:15:00"),
        status: "warning",
        insights: [
          "Compliance with ISO 9001 standards confirmed",
          "Environmental impact assessment pending",
          "Safety protocols need additional detail",
        ],
      },
      {
        id: "ar3",
        title: "Initial Document Processing",
        summary:
          "Successfully extracted and indexed 47 pages from 2 PDF documents. Key sections identified: Executive Summary, Technical Specifications, Budget Overview, Timeline.",
        date: new Date("2024-01-25T11:00:00"),
        status: "info",
        insights: [
          "2 documents processed successfully",
          "47 pages indexed",
          "4 key sections identified",
        ],
      },
    ],
  },
  t2: {
    id: "t2",
    title: "Bridge Renovation Project",
    spaceName: "Government Infrastructure Projects",
    spaceId: "1",
    status: "in-progress",
    createdAt: new Date("2024-02-01"),
    files: [{ name: "Project_Scope.pdf", type: "pdf" }],
    analysisResults: [
      {
        id: "ar4",
        title: "Scope Analysis In Progress",
        summary:
          "Currently analyzing project scope document. Preliminary findings suggest a 12-month timeline with 3 major milestones.",
        date: new Date("2024-02-20T16:45:00"),
        status: "info",
        insights: [
          "12-month estimated timeline",
          "3 major milestones identified",
          "Detailed breakdown pending",
        ],
      },
    ],
  },
  t3: {
    id: "t3",
    title: "MRI Machine Acquisition",
    spaceName: "Healthcare Equipment Procurement",
    spaceId: "2",
    status: "draft",
    createdAt: new Date("2024-02-15"),
    files: [],
    analysisResults: [],
  },
  t4: {
    id: "t4",
    title: "Cloud Migration Services",
    spaceName: "IT Services & Software",
    spaceId: "3",
    status: "completed",
    createdAt: new Date("2024-03-05"),
    files: [
      { name: "RFP_Document.pdf", type: "pdf" },
      { name: "Vendor_Responses.pdf", type: "pdf" },
      { name: "Evaluation_Matrix.pdf", type: "pdf" },
    ],
    analysisResults: [
      {
        id: "ar5",
        title: "Final Vendor Evaluation Complete",
        summary:
          "Analysis complete. Top 3 vendors identified based on technical capability, pricing, and service level agreements. Recommended vendor: CloudTech Solutions.",
        date: new Date("2024-04-01T10:00:00"),
        status: "success",
        insights: [
          "CloudTech Solutions recommended as primary vendor",
          "25% cost savings compared to average quotes",
          "All SLA requirements met or exceeded",
        ],
      },
      {
        id: "ar6",
        title: "Vendor Response Analysis",
        summary:
          "Analyzed 8 vendor responses. All vendors meet minimum technical requirements. Pricing varies from $150K to $280K annual cost.",
        date: new Date("2024-03-25T14:20:00"),
        status: "info",
        insights: [
          "8 vendors responded to RFP",
          "Price range: $150K - $280K annually",
          "All meet minimum requirements",
        ],
      },
      {
        id: "ar7",
        title: "RFP Requirements Extracted",
        summary:
          "Successfully extracted 32 technical requirements and 15 compliance requirements from RFP document. Evaluation matrix prepared.",
        date: new Date("2024-03-10T09:30:00"),
        status: "success",
        insights: [
          "32 technical requirements identified",
          "15 compliance requirements identified",
          "Evaluation matrix generated",
        ],
      },
    ],
  },
  t5: {
    id: "t5",
    title: "Cybersecurity Assessment",
    spaceName: "IT Services & Software",
    spaceId: "3",
    status: "in-progress",
    createdAt: new Date("2024-03-10"),
    files: [{ name: "Security_Requirements.pdf", type: "pdf" }],
    analysisResults: [
      {
        id: "ar8",
        title: "Security Requirements Analysis",
        summary:
          "Identified 28 security controls required. Analysis shows alignment with NIST framework. Risk assessment in progress.",
        date: new Date("2024-03-18T11:15:00"),
        status: "warning",
        insights: [
          "28 security controls required",
          "NIST framework compliance confirmed",
          "3 high-priority controls flagged",
        ],
      },
    ],
  },
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

function getResultIcon(status: string) {
  switch (status) {
    case "success":
      return <CheckCircle className="h-5 w-5 text-green-600" />
    case "warning":
      return <AlertCircle className="h-5 w-5 text-amber-500" />
    case "info":
      return <Clock className="h-5 w-5 text-sky-500" />
    default:
      return <Clock className="h-5 w-5 text-muted-foreground" />
  }
}

function getResultHeaderBg(status: string) {
  switch (status) {
    case "success":
      return "bg-green-50 border-green-200"
    case "warning":
      return "bg-amber-50 border-amber-200"
    case "info":
      return "bg-sky-50 border-sky-200"
    default:
      return "bg-muted border-border"
  }
}

export default function TenderAnalysisPage({
  params,
}: {
  params: Promise<{ spaceId: string; tenderId: string }>
}) {
  const { spaceId, tenderId } = use(params)
  const tender = tendersData[tenderId] || {
    id: tenderId,
    title: "Unknown Tender",
    spaceName: "Unknown Space",
    spaceId: spaceId,
    status: "draft" as const,
    createdAt: new Date(),
    files: [],
    analysisResults: [],
  }

  const sortedResults = [...tender.analysisResults].sort(
    (a, b) => b.date.getTime() - a.date.getTime()
  )

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-background flex flex-col">
      <DashboardHeader />

      <main className="max-w-4xl mx-auto px-6 py-10 flex-1 w-full">
        <Breadcrumb className="mb-8">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="/dashboard" className="text-muted-foreground hover:text-foreground">
                Home
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink
                href={`/space/${tender.spaceId}`}
                className="text-muted-foreground hover:text-foreground"
              >
                {tender.spaceName}
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className="text-foreground font-medium">
                {tender.title}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        <Card className="border-border rounded-xl bg-card mb-8">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-2xl text-foreground">
                  {tender.title}
                </CardTitle>
                <p className="text-muted-foreground mt-2">
                  Created {format(tender.createdAt, "MMMM d, yyyy")}
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
                {tender.files.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No files uploaded</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {tender.files.map((file) => (
                      <div
                        key={file.name}
                        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border"
                      >
                        <FileText className="h-4 w-4 text-red-500" />
                        <span className="text-sm text-foreground">{file.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-6 pt-2">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {tender.analysisResults.length} analysis result
                    {tender.analysisResults.length !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm text-muted-foreground">
                    {tender.files.length} file{tender.files.length !== 1 ? "s" : ""}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Analysis Results</h2>
          {sortedResults.length === 0 ? (
            <Card className="border-border rounded-xl bg-card">
              <CardContent className="py-16 text-center">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-lg text-muted-foreground">No analysis results yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Upload files to begin automated analysis
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {sortedResults.map((result) => (
                <Card
                  key={result.id}
                  className="border-border rounded-xl bg-card overflow-hidden"
                >
                  <div
                    className={`px-6 py-4 border-b ${getResultHeaderBg(result.status)}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getResultIcon(result.status)}
                        <h3 className="font-semibold text-foreground">
                          {result.title}
                        </h3>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        {format(result.date, "MMM d, yyyy 'at' h:mm a")}
                      </span>
                    </div>
                  </div>
                  <CardContent className="pt-5">
                    <p className="text-foreground leading-relaxed mb-4">
                      {result.summary}
                    </p>
                    {result.insights.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-muted-foreground">
                          Key Insights
                        </h4>
                        <ul className="space-y-1">
                          {result.insights.map((insight, index) => (
                            <li
                              key={index}
                              className="flex items-start gap-2 text-sm text-foreground"
                            >
                              <span className="text-accent-foreground mt-1">•</span>
                              {insight}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

      <DashboardFooter />
      <ChatbotWidget />
    </div>
    </ProtectedRoute>
  )
}
