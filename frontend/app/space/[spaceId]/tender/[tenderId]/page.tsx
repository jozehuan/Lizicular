"use client"

import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input" // Import Input component
import { Button } from "@/components/ui/button" // Import Button component
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog" // Import Dialog components
import { Label } from "@/components/ui/label" // Import Label component
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog" // Import AlertDialog components
import {
  FileText,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Plus, // Import Plus icon
  Upload, // Import Upload icon
  X, // Import X icon
} from "lucide-react"
import { useState, useRef, use, useMemo, useCallback, useEffect } from "react" // Import useRef, useLayoutEffect, useMemo
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

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

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
  status: "pending" | "processing" | "completed" | "failed" | string
  data: any // Keeping this generic for now, as AnalysisDisplay handles the details
  error_message?: string
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

interface Automation {
  id: string
  name: string
  description: string | null
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
    const { user, accessToken, isLoading: isAuthLoading } = useAuth() // Get user and accessToken from useAuth
  const [tender, setTender] = useState<TenderData | null>(null)
  const [workspaceName, setWorkspaceName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditingTenderName, setIsEditingTenderName] = useState(false) // State for inline editing
  const [newTenderName, setNewTenderName] = useState("") // New tender name during editing
  const [currentMemberRole, setCurrentMemberRole] = useState<string | null>(null) // User's role in the workspace

  const [resultToDeleteId, setResultToDeleteId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [automations, setAutomations] = useState<Automation[]>([]);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [newAnalysisName, setNewAnalysisName] = useState("");
  const [selectedAutomationId, setSelectedAutomationId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);

  const canEditTender = useMemo(() => {
    const editableRoles = ["OWNER", "ADMIN", "EDITOR"];
    return currentMemberRole ? editableRoles.includes(currentMemberRole) : false;
  }, [currentMemberRole]);

  const fetchTenderAndWorkspaceData = useCallback(async () => {
    if (!accessToken || !user?.id || isAuthLoading) {
      // Don't set error here, let the auth state settle
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Fetch all data in parallel
      const [tenderRes, workspaceRes, automationsRes] = await Promise.all([
        fetch(`${API_URL}/tenders/${tenderId}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
        fetch(`${API_URL}/workspaces/${spaceId}`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
        fetch(`${API_URL}/automations/`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        }),
      ]);

      if (!tenderRes.ok) {
        const errorData = await tenderRes.json();
        throw new Error(errorData.detail || "Failed to fetch tender.");
      }
      const tenderData: TenderData = await tenderRes.json();
      
      // Create a new, immutable version of the analysis results by patching missing data
      const results = tenderData.analysis_results || [];
      const patchedResults = await Promise.all(results.map(async (result) => {
        if (result.status === 'completed' && !result.data) {
          try {
            const analysisRes = await fetch(`${API_URL}/analysis-results/${result.id}`, {
              headers: { Authorization: `Bearer ${accessToken}` },
            });
            if (analysisRes.ok) {
              const fullAnalysisData = await analysisRes.json();
              return { ...result, data: fullAnalysisData }; // Return a new object
            }
          } catch (patchError) {
            console.error(`Failed to patch analysis data for ${result.id}:`, patchError);
          }
        }
        return result; // Return the original result if no patching is needed
      }));

      const updatedTenderData = { ...tenderData, analysis_results: patchedResults };

      setTender(updatedTenderData);
      setNewTenderName(updatedTenderData.name);

      if (!workspaceRes.ok) {
        const errorData = await workspaceRes.json();
        throw new Error(errorData.detail || "Failed to fetch workspace.");
      }
      const workspaceData = await workspaceRes.json();
      setWorkspaceName(workspaceData.name);

      const currentUserMembership = workspaceData.members.find(
        (member: any) => member.user_id === user.id
      );
      setCurrentMemberRole(currentUserMembership ? currentUserMembership.role : null);

      if (!automationsRes.ok) {
        const errorData = await automationsRes.json();
        throw new Error(errorData.detail || "Failed to fetch automations.");
      }
      const automationsData: Automation[] = await automationsRes.json();
      setAutomations(automationsData);

    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  }, [spaceId, tenderId, accessToken, user?.id, isAuthLoading]);


  useEffect(() => {
    fetchTenderAndWorkspaceData();
  }, [fetchTenderAndWorkspaceData]);

  // WebSocket logic for real-time analysis updates
  useEffect(() => {
    if (!tender?.analysis_results) return;

    const sockets: WebSocket[] = [];

    tender.analysis_results.forEach(result => {
      if (result.status === 'pending' || result.status === 'processing') {
        const wsUrl = API_URL.replace(/^http/, 'ws') + `/ws/analysis/${result.id}`;
        
        try {
          const ws = new WebSocket(wsUrl);

          ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.status === 'COMPLETED' || message.status === 'FAILED') {
              // Refetch all data to ensure UI is in sync with the database
              fetchTenderAndWorkspaceData();
            }
          };

          ws.onerror = (error) => {
            console.error(`WebSocket error for analysis ${result.id}:`, error);
          };
          
          sockets.push(ws);

        } catch (error) {
          console.error(`Failed to create WebSocket for analysis ${result.id}:`, error);
        }
      }
    });

    // Cleanup on component unmount
    return () => {
      sockets.forEach(ws => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      });
    };
  }, [tender?.analysis_results, fetchTenderAndWorkspaceData]);

  // Refetch data when the tab becomes visible again to ensure freshness
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchTenderAndWorkspaceData();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchTenderAndWorkspaceData]);


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

  const handleDeleteAnalysisClick = (analysisId: string) => {
    setResultToDeleteId(analysisId);
  };

  const handleConfirmDelete = async () => {
    if (!resultToDeleteId || !tender) return;

    setIsDeleting(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/tenders/${tender.id}/analysis/${resultToDeleteId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete analysis result.");
      }

      // Refresh data to show updated list
      await fetchTenderAndWorkspaceData();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
      setResultToDeleteId(null);
    }
  };

  const handleGenerateAnalysis = async () => {
    if (!selectedAutomationId) {
      setGenerateError("Please select an automation.");
      return;
    }

    setIsGenerating(true);
    setGenerateError(null);

    try {
      let finalName = newAnalysisName.trim();
      if (!finalName) {
        const selectedAutomation = automations.find(a => a.id === selectedAutomationId);
        const automationName = selectedAutomation?.name || "Analysis";
        finalName = `${automationName} - ${format(new Date(), "yyyy-MM-dd HH:mm")}`;
      }

      const response = await fetch(`${API_URL}/tenders/${tenderId}/generate_analysis`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({
          automation_id: selectedAutomationId,
          name: finalName,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to start analysis generation.");
      }

      // Success
      setShowGenerateDialog(false);
      setNewAnalysisName("");
      setSelectedAutomationId(null);
      await fetchTenderAndWorkspaceData(); // Refresh data to show pending analysis

    } catch (err: any) {
      setGenerateError(err.message);
    } finally {
      setIsGenerating(false);
    }
  };


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
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-foreground">
                Analysis Results
              </h2>
              {canEditTender && (
                <Button onClick={() => setShowGenerateDialog(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Generate Analysis
                </Button>
              )}
            </div>
            <AnalysisDisplay 
              analysisResults={tender.analysis_results} 
              onDelete={handleDeleteAnalysisClick}
              spaceId={spaceId}
              tenderId={tenderId}
            />
          </div>
        </main>

        <DashboardFooter />
        <ChatbotWidget />
      </div>

      {/* Add Files Dialog */}
      <Dialog open={showAddFileDialog} onOpenChange={setShowAddFileDialog}>
        {/* ... Dialog content is unchanged ... */}
      </Dialog>

      {/* Generate Analysis Dialog */}
      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent className="rounded-xl border-border bg-card">
          <DialogHeader>
            <DialogTitle>Generate New Analysis</DialogTitle>
            <DialogDescription>
              Select an automation and provide a name for this analysis run.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {generateError && (
               <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {generateError}
              </div>
            )}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="analysis-name" className="text-right">
                Name
              </Label>
              <Input
                id="analysis-name"
                value={newAnalysisName}
                onChange={(e) => setNewAnalysisName(e.target.value)}
                placeholder="Optional, e.g., 'Initial Price Check'"
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="automation" className="text-right">
                Automation
              </Label>
              <Select onValueChange={setSelectedAutomationId} value={selectedAutomationId || undefined}>
                <SelectTrigger className="col-span-3">
                  <SelectValue placeholder="Select an automation" />
                </SelectTrigger>
                <SelectContent>
                  {automations.map((auto) => (
                    <SelectItem key={auto.id} value={auto.id}>
                      {auto.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGenerateDialog(false)}>Cancel</Button>
            <Button onClick={handleGenerateAnalysis} disabled={!selectedAutomationId || isGenerating}>
              {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Generate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

       <AlertDialog open={!!resultToDeleteId} onOpenChange={(open) => !open && setResultToDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete this analysis result.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setResultToDeleteId(null)} disabled={isDeleting}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} disabled={isDeleting} className="bg-destructive hover:bg-destructive/90">
              {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ProtectedRoute>
  )
}
