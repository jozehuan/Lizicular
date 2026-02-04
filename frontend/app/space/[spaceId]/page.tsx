"use client"

import React from "react"
import { use, useState, useRef } from "react"
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
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { FileText, Upload, X, Plus, Calendar, Users, FolderOpen } from "lucide-react"

interface TenderFile {
  name: string
  size: string
}

interface Tender {
  id: string
  title: string
  status: "draft" | "in-progress" | "analyzed" | "completed"
  files: TenderFile[]
  createdAt: Date
}

interface Member {
  id: string
  name: string
  email: string
  role: "owner" | "admin" | "editor" | "viewer"
  avatar?: string
}

interface SpaceData {
  name: string
  createdAt: Date
  members: Member[]
  tenders: Tender[]
}

const spacesData: Record<string, SpaceData> = {
  "1": {
    name: "Government Infrastructure Projects",
    createdAt: new Date("2024-01-15"),
    members: [
      { id: "m1", name: "Carlos García", email: "carlos@example.com", role: "owner" },
      { id: "m2", name: "María López", email: "maria@example.com", role: "admin" },
      { id: "m3", name: "Juan Martínez", email: "juan@example.com", role: "editor" },
      { id: "m4", name: "Ana Rodríguez", email: "ana@example.com", role: "viewer" },
    ],
    tenders: [
      {
        id: "t1",
        title: "Highway Construction Tender 2024",
        status: "analyzed",
        files: [
          { name: "Technical_Requirements.pdf", size: "2.4 MB" },
          { name: "Budget_Proposal.pdf", size: "1.8 MB" },
        ],
        createdAt: new Date("2024-01-20"),
      },
      {
        id: "t2",
        title: "Bridge Renovation Project",
        status: "in-progress",
        files: [{ name: "Project_Scope.pdf", size: "3.1 MB" }],
        createdAt: new Date("2024-02-01"),
      },
    ],
  },
  "2": {
    name: "Healthcare Equipment Procurement",
    createdAt: new Date("2024-02-10"),
    members: [
      { id: "m5", name: "Elena Sánchez", email: "elena@example.com", role: "owner" },
      { id: "m6", name: "Pedro Díaz", email: "pedro@example.com", role: "editor" },
    ],
    tenders: [
      {
        id: "t3",
        title: "MRI Machine Acquisition",
        status: "draft",
        files: [],
        createdAt: new Date("2024-02-15"),
      },
    ],
  },
  "3": {
    name: "IT Services & Software",
    createdAt: new Date("2024-03-01"),
    members: [
      { id: "m7", name: "Laura Fernández", email: "laura@example.com", role: "owner" },
      { id: "m8", name: "Miguel Torres", email: "miguel@example.com", role: "admin" },
      { id: "m9", name: "Isabel Ruiz", email: "isabel@example.com", role: "viewer" },
    ],
    tenders: [
      {
        id: "t4",
        title: "Cloud Migration Services",
        status: "completed",
        files: [
          { name: "RFP_Document.pdf", size: "4.2 MB" },
          { name: "Vendor_Responses.pdf", size: "8.7 MB" },
          { name: "Evaluation_Matrix.pdf", size: "1.1 MB" },
        ],
        createdAt: new Date("2024-03-05"),
      },
      {
        id: "t5",
        title: "Cybersecurity Assessment",
        status: "in-progress",
        files: [{ name: "Security_Requirements.pdf", size: "2.9 MB" }],
        createdAt: new Date("2024-03-10"),
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

function getRoleColor(role: string) {
  switch (role) {
    case "owner":
      return "bg-primary text-primary-foreground"
    case "admin":
      return "bg-accent text-accent-foreground"
    case "editor":
      return "bg-secondary text-secondary-foreground"
    case "viewer":
      return "bg-muted text-muted-foreground"
    default:
      return "bg-muted text-muted-foreground"
  }
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

interface NewTenderDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (name: string, files: File[]) => void
}

function NewTenderDialog({ isOpen, onClose, onSubmit }: NewTenderDialogProps) {
  const [tenderName, setTenderName] = useState("")
  const [files, setFiles] = useState<File[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files).filter(
      (file) => file.type === "application/pdf"
    )
    setFiles((prev) => [...prev, ...droppedFiles])
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...selectedFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = () => {
    if (tenderName.trim()) {
      onSubmit(tenderName, files)
      setTenderName("")
      setFiles([])
      onClose()
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B"
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
    return (bytes / (1024 * 1024)).toFixed(1) + " MB"
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="rounded-xl border-border bg-card max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">Create New Tender</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            Add a new tender to this workspace with its documents
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6 pt-4">
          <div className="space-y-2">
            <Label htmlFor="tender-name" className="text-foreground">
              Tender Name
            </Label>
            <Input
              id="tender-name"
              value={tenderName}
              onChange={(e) => setTenderName(e.target.value)}
              placeholder="Enter tender name..."
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-foreground">Documents</Label>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
                ${
                  isDragging
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50 hover:bg-muted/50"
                }
              `}
            >
              <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-foreground font-medium">
                Drag and drop PDF files here
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                or click to browse from your computer
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <Label className="text-foreground">
                Selected Files ({files.length})
              </Label>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {files.map((file, index) => (
                  <div
                    key={`${file.name}-${index}`}
                    className="flex items-center justify-between p-3 rounded-xl border border-border bg-muted/50"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-red-500 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="text-sm text-foreground truncate max-w-[250px]">
                          {file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        removeFile(index)
                      }}
                      className="text-muted-foreground hover:text-destructive transition-colors p-1"
                      aria-label={`Remove ${file.name}`}
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!tenderName.trim()}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Create Tender
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default function SpaceDetailPage({
  params,
}: {
  params: Promise<{ spaceId: string }>
}) {
  const { spaceId } = use(params)
  const space = spacesData[spaceId] || {
    name: "Unknown Space",
    createdAt: new Date(),
    members: [],
    tenders: [],
  }
  const [tenders, setTenders] = useState<Tender[]>(space.tenders)
  const [isNewTenderOpen, setIsNewTenderOpen] = useState(false)

  const handleCreateTender = (name: string, files: File[]) => {
    const newTender: Tender = {
      id: `t${Date.now()}`,
      title: name,
      status: "draft",
      files: files.map((f) => ({
        name: f.name,
        size: `${(f.size / (1024 * 1024)).toFixed(1)} MB`,
      })),
      createdAt: new Date(),
    }
    setTenders([newTender, ...tenders])
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
              <BreadcrumbPage className="text-foreground font-medium">
                {space.name}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Workspace Info */}
        <Card className="border-border rounded-xl bg-card mb-8">
          <CardHeader className="pb-4">
            <CardTitle className="text-2xl text-foreground">{space.name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span className="text-sm">
                Created on {format(space.createdAt, "MMMM d, yyyy")}
              </span>
            </div>

            {/* Members Section */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-foreground">
                <Users className="h-4 w-4" />
                <span className="font-medium">
                  Members ({space.members.length})
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {space.members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 p-3 rounded-xl border border-border bg-muted/30"
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarFallback className="bg-primary/10 text-primary text-sm">
                        {getInitials(member.name)}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {member.name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {member.email}
                      </p>
                    </div>
                    <Badge
                      className={`rounded-lg text-xs capitalize ${getRoleColor(member.role)}`}
                    >
                      {member.role}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tenders Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">
              Tenders ({tenders.length})
            </h2>
            <Button
              onClick={() => setIsNewTenderOpen(true)}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              New Tender
            </Button>
          </div>

          {tenders.length === 0 ? (
            <Card className="border-border rounded-xl bg-card">
              <CardContent className="py-16 text-center">
                <FolderOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-lg text-muted-foreground">No tenders yet</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Create your first tender to get started
                </p>
              </CardContent>
            </Card>
          ) : (
            <Accordion type="single" collapsible className="space-y-3">
              {tenders.map((tender) => (
                <AccordionItem
                  key={tender.id}
                  value={tender.id}
                  className="border border-border rounded-xl bg-card px-0 overflow-hidden"
                >
                  <AccordionTrigger className="px-6 py-5 hover:no-underline hover:bg-muted/50 [&[data-state=open]]:border-b [&[data-state=open]]:border-border">
                    <div className="flex items-center justify-between w-full pr-4">
                      <div className="flex flex-col items-start text-left">
                        <span className="text-lg font-medium text-foreground">
                          {tender.title}
                        </span>
                        <span className="text-sm text-muted-foreground mt-1">
                          Created {format(tender.createdAt, "MMM d, yyyy")} &middot;{" "}
                          {tender.files.length} document
                          {tender.files.length !== 1 ? "s" : ""}
                        </span>
                      </div>
                      <Badge
                        className={`rounded-lg ml-4 ${getStatusColor(tender.status)}`}
                      >
                        {formatStatus(tender.status)}
                      </Badge>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="px-6 pb-5 pt-4">
                    {tender.files.length === 0 ? (
                      <p className="text-muted-foreground text-sm py-4 text-center">
                        No documents uploaded yet
                      </p>
                    ) : (
                      <div className="space-y-2">
                        <p className="text-sm font-medium text-muted-foreground mb-3">
                          Uploaded Documents
                        </p>
                        {tender.files.map((file) => (
                          <div
                            key={file.name}
                            className="flex items-center justify-between p-3 rounded-xl border border-border bg-muted/30"
                          >
                            <div className="flex items-center gap-3">
                              <FileText className="h-5 w-5 text-red-500" />
                              <span className="text-sm text-foreground">
                                {file.name}
                              </span>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {file.size}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="mt-4 pt-4 border-t border-border">
                      <Link
                        href={`/space/${spaceId}/tender/${tender.id}`}
                        className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                      >
                        View Analysis Results
                        <span aria-hidden="true">&rarr;</span>
                      </Link>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
        </div>
      </main>

      <NewTenderDialog
        isOpen={isNewTenderOpen}
        onClose={() => setIsNewTenderOpen(false)}
        onSubmit={handleCreateTender}
      />

      <DashboardFooter />
      <ChatbotWidget />
    </div>
    </ProtectedRoute>
  )
}
