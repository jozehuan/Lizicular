"use client"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input" // Import Input component
import { Button } from "@/components/ui/button" // Import Button component
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog" // Import Dialog components
import { Label } from "@/components/ui/label" // Import Label component
import {
  FileText,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Plus, // Import Plus icon
  Upload, // Import Upload icon
  X, // Import X icon
} from "lucide-react"
import { useState, useRef, use, useLayoutEffect, useMemo } from "react" // Import useRef, useLayoutEffect, useMemo
import Link from "next/link"

import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle
} from "@/components/ui/card"
import { format } from "date-fns"
import { useAuth } from "@/lib/auth-context"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { DashboardFooter } from "@/components/dashboard/footer"
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget"
import { AnalysisDisplay } from "@/components/tender/analysis-display"

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000" // Define API_URL here

// Interfaces matching the backend schema
interface TenderDocument {
  id: string; // Add id to TenderDocument for removal
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
  const { spaceId, tenderId } = use(params)
  const { user, accessToken } = useAuth() // Get user and accessToken from useAuth
  const [tender, setTender] = useState<TenderData | null>(null)
  const [workspaceName, setWorkspaceName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditingTenderName, setIsEditingTenderName] = useState(false) // State for inline editing
  const [newTenderName, setNewTenderName] = useState("") // New tender name during editing
  const [currentMemberRole, setCurrentMemberRole] = useState<string | null>(null) // User's role in the workspace

  const canEditTender = useMemo(() => {
    const editableRoles = ["OWNER", "ADMIN", "EDITOR"];
    return currentMemberRole ? editableRoles.includes(currentMemberRole) : false;
  }, [currentMemberRole]);

  const handleUpdateTenderName = async () => {
    if (!tender || !accessToken || newTenderName === tender.name) {
      setIsEditingTenderName(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/tenders/${tender.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ name: newTenderName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update tender name.");
      }

      const updatedTender: TenderData = await response.json();
      setTender(updatedTender);
      setIsEditingTenderName(false);
      setError(null);
    } catch (err: any) {
      setError(err.message || "An error occurred while updating tender name.");
      // Revert to original name on error
      setNewTenderName(tender.name);
      setIsEditingTenderName(false);
    }
  };


  const [showAddFileDialog, setShowAddFileDialog] = useState(false); // State for file upload dialog
  const [filesToUpload, setFilesToUpload] = useState<File[]>([]); // Files selected for upload
  const [isUploadingFiles, setIsUploadingFiles] = useState(false); // Loading state for file upload
  const [uploadError, setUploadError] = useState<string | null>(null); // Error for file upload

  const fileInputRef = useRef<HTMLInputElement>(null); // Ref for hidden file input

  // Fetch tender and workspace data
  useLayoutEffect(() => {
    const fetchTenderAndWorkspaceData = async () => {
      if (!accessToken || !user?.id) {
        setError("Authentication required.");
        setLoading(false);
        return;
      }

      try {
        // Fetch tender data
        const tenderResponse = await fetch(`${API_URL}/tenders/${tenderId}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        if (!tenderResponse.ok) {
          const errorData = await tenderResponse.json();
          throw new Error(errorData.detail || "Failed to fetch tender.");
        }
        const tenderData: TenderData = await tenderResponse.json();
        setTender(tenderData);
        setNewTenderName(tenderData.name); // Initialize newTenderName

        // Fetch workspace data to get the name and user's role
        const workspaceResponse = await fetch(`${API_URL}/workspaces/${spaceId}`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        if (!workspaceResponse.ok) {
          const errorData = await workspaceResponse.json();
          throw new Error(errorData.detail || "Failed to fetch workspace.");
        }
        const workspaceData = await workspaceResponse.json();
        setWorkspaceName(workspaceData.name);

        // Determine current user's role in the workspace
        const currentUserMembership = workspaceData.members.find(
          (member: any) => member.user_id === user.id
        );
        if (currentUserMembership) {
          setCurrentMemberRole(currentUserMembership.role);
        } else {
          setCurrentMemberRole(null); // User is not a member of this workspace
        }
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    };

    fetchTenderAndWorkspaceData();
  }, [spaceId, tenderId, accessToken, user?.id]);

  // Function to handle adding files
  const handleAddFiles = async () => {
    if (!tender || filesToUpload.length === 0) {
      setUploadError("No files selected for upload.");
      return;
    }
    if (!accessToken) {
      setUploadError("Authentication token missing.");
      return;
    }

    setIsUploadingFiles(true);
    setUploadError(null);

    try {
      const formData = new FormData();
      filesToUpload.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${API_URL}/tenders/${tender.id}/documents`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          // Content-Type is set automatically by FormData
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to upload files.");
      }

      const updatedTender = await response.json();
      setTender(updatedTender); // Update tender state with new documents
      setShowAddFileDialog(false); // Close dialog
      setFilesToUpload([]); // Clear selected files
      setError(null); // Clear any main error
    } catch (err: any) {
      setUploadError(err.message || "An error occurred during file upload.");
    } finally {
      setIsUploadingFiles(false);
    }
  };

  // Function to handle removing a document
  const handleRemoveDocument = async (documentId: string) => {
    if (!tender) return;
    if (!accessToken) {
      setUploadError("Authentication token missing.");
      return;
    }

    try {
      const response = await fetch(`${API_URL}/tenders/${tender.id}/documents/${documentId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to remove document.");
      }

      const updatedTender = await response.json();
      setTender(updatedTender); // Update tender state with document removed
      setError(null); // Clear any main error
    } catch (err: any) {
      setError(err.message || "An error occurred during document removal.");
    }
  };
  
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
        <Link href="/dashboard" className="mt-4 text-blue-500 hover:underline">
          Go to Dashboard
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
        {/* <DashboardHeader /> REMOVED: Header is provided by RootLayout */}

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
                  {workspaceName || spaceId} 
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
                  {isEditingTenderName && canEditTender ? (
                    <Input
                      value={newTenderName}
                      onChange={(e) => setNewTenderName(e.target.value)}
                      onBlur={handleUpdateTenderName}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          handleUpdateTenderName();
                        }
                        if (e.key === "Escape") {
                          setIsEditingTenderName(false);
                          setNewTenderName(tender?.name || "");
                        }
                      }}
                      className="h-9 text-2xl font-semibold bg-background"
                    />
                  ) : (
                    <CardTitle
                      className="text-2xl text-foreground flex items-baseline gap-2 cursor-pointer"
                      onDoubleClick={() => canEditTender && setIsEditingTenderName(true)}
                    >
                      {tender.name}
                    </CardTitle>
                  )}
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
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">
                      Attached Files
                    </h3>
                    {canEditTender && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowAddFileDialog(true)}
                        className="h-7 px-3 text-muted-foreground hover:text-foreground"
                      >
                        <Plus className="h-4 w-4 mr-1" /> Add Files
                      </Button>
                    )}
                  </div>
                  {tender.documents.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No files uploaded
                    </p>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {tender.documents.map((file) => (
                        <div
                          key={file.id} // Use file.id as key if available and unique
                          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border"
                        >
                          <FileText className="h-4 w-4 text-red-500" />
                          <span className="text-sm text-foreground">
                            {file.filename}
                          </span>
                          {canEditTender && ( // Show delete button if user can edit
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleRemoveDocument(file.id)}
                              className="h-6 w-6 text-muted-foreground hover:text-destructive"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
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

      {/* Add Files Dialog */}
      <Dialog open={showAddFileDialog} onOpenChange={setShowAddFileDialog}>
        <DialogContent className="rounded-xl border-border bg-card max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-foreground">Add Documents to Tender</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Drag and drop PDF files or click to select them to add to this tender.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            {uploadError && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {uploadError}
              </div>
            )}
            <div
              onDragOver={(e) => { e.preventDefault(); /* setIsDragging(true); */ }}
              onDragLeave={(e) => { e.preventDefault(); /* setIsDragging(false); */ }}
              onDrop={(e) => {
                e.preventDefault();
                // setIsDragging(false);
                const droppedFiles = Array.from(e.dataTransfer.files);
                setFilesToUpload((prev) => [...prev, ...droppedFiles]);
              }}
              onClick={() => fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors
                border-border hover:border-primary/50 hover:bg-muted/50
              `}
            >
              <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-foreground font-medium">
                Drag and drop files here
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                or click to browse from your computer
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf" // Assuming only PDF files are allowed
                onChange={(e) => {
                  if (e.target.files) {
                    setFilesToUpload((prev) => [...prev, ...Array.from(e.target.files)]);
                  }
                }}
                className="hidden"
                disabled={isUploadingFiles}
              />
            </div>

            {filesToUpload.length > 0 && (
              <div className="space-y-2">
                <Label className="text-foreground">
                  Selected Files ({filesToUpload.length})
                </Label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {filesToUpload.map((file, index) => (
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
                            {file.size ? (file.size / 1024).toFixed(1) + " KB" : ""}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setFilesToUpload((prev) => prev.filter((_, i) => i !== index));
                        }}
                        className="text-muted-foreground hover:text-destructive transition-colors p-1"
                        aria-label={`Remove ${file.name}`}
                        disabled={isUploadingFiles}
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
                onClick={() => {
                  setShowAddFileDialog(false);
                  setFilesToUpload([]);
                  setUploadError(null);
                }}
                disabled={isUploadingFiles}
                className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent"
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddFiles}
                disabled={filesToUpload.length === 0 || isUploadingFiles}
                className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
              >
                {isUploadingFiles ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Upload Documents"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </ProtectedRoute>
  )
}
