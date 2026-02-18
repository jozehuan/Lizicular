"use client"

import React from "react"
import { useState, useEffect, useCallback, useRef, use } from "react" // Use useEffect and useCallback
import Link from "next/link"
import { format } from "date-fns"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
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
import { FileText, Upload, X, Plus, Calendar, Users, FolderOpen, Loader2, AlertCircle, Trash2 } from "lucide-react" // Add Loader2, AlertCircle, Trash2
import { useAuth } from "@/lib/auth-context" // Import useAuth
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

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

const HexagonIcon = (props: React.SVGProps<SVGSVGElement>) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
  </svg>
)

import { getStatusBadgeClasses } from "@/lib/style-utils"

// Updated interfaces to match backend
export interface FrontendTenderDocument {
  id: string;
  filename: string;
  content_type: string;
  size: number;
  // Add other fields from backend TenderDocument if needed for display
}

export interface Tender { // Aligned with backend's Tender schema
  id: string
  name: string // Use 'name' instead of 'title'
  description?: string
  workspace_id: string
  status: string // This can be deprecated on the frontend later
  documents?: FrontendTenderDocument[]
  analysis_results?: { status: string }[] // Add analysis results
  created_at: string
  updated_at: string
}

export interface Member { // Aligned with WorkspaceMemberResponse
  id: string // User's ID
  name: string // User's full_name
  email: string
  role: string // WorkspaceRole is string
  avatar?: string // Frontend specific
}

export interface WorkspaceData { // Aligned with WorkspaceResponse
  id: string
  name: string
  description: string
  owner_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

// Remove mock spacesData

function getRoleColor(role: string) {
  switch (role.toLowerCase()) { // Use toLowerCase to match backend enum
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

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return bytes + " B"
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB"
  return (bytes / (1024 * 1024)).toFixed(1) + " MB"
}

interface NewTenderDialogProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (tenderName: string, files: File[], spaceId: string) => Promise<void>
  spaceId: string // Pass spaceId
  isSubmitting: boolean
  error: string | null
}

function NewTenderDialog({ isOpen, onClose, onSubmit, spaceId, isSubmitting, error }: NewTenderDialogProps) { // Receive spaceId
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
      onSubmit(tenderName, files, spaceId) // Pass spaceId to onSubmit
      setTenderName("")
      setFiles([])
      // onClose() // Do not close immediately, let parent handle it based on submission success
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
            {error && ( // Display error message if present
            <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
            </div>
            )}
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
              disabled={isSubmitting}
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
              aria-disabled={isSubmitting}
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
                disabled={isSubmitting}
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
                      disabled={isSubmitting}
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
              disabled={isSubmitting}
              className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent"
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!tenderName.trim() || isSubmitting}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Tender"
              )}
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
  params: Promise<{ spaceId: string }> // Changed back to Promise
}) {
  const { spaceId } = use(params) // Unwrap params with use()
  const { user, accessToken, isLoading: isAuthLoading } = useAuth() // Get the user object
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [tenders, setTenders] = useState<Tender[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isNewTenderOpen, setIsNewTenderOpen] = useState(false)
  const [isCreatingTender, setIsCreatingTender] = useState(false)
  const [createTenderError, setCreateTenderError] = useState<string | null>(null)
  const [showDeleteTenderConfirm, setShowDeleteTenderConfirm] = useState(false) // State for tender delete confirmation dialog
  const [tenderToDeleteId, setTenderToDeleteId] = useState<string | null>(null) // State to store ID of tender to delete

  const [isEditingWorkspaceName, setIsEditingWorkspaceName] = useState(false); // State for inline editing of workspace name
  const [newWorkspaceName, setNewWorkspaceName] = useState(workspace?.name || ""); // Holds the new name during editing

  const [showNewCollaboratorForm, setShowNewCollaboratorForm] = useState(false); // State to show/hide new collaborator form
  const [newCollaboratorEmail, setNewCollaboratorEmail] = useState(""); // Email for new collaborator
  const [newCollaboratorRole, setNewCollaboratorRole] = useState("VIEWER"); // Role for new collaborator
  const [addCollaboratorError, setAddCollaboratorError] = useState<string | null>(null); // New state for inline error

  // Derived state to check if current user is owner or admin
  const currentUserIsOwner = members.find(m => m.id === user?.id)?.role === "OWNER";
  const currentUserIsAdmin = members.find(m => m.id === user?.id)?.role === "ADMIN";
  const canEditWorkspaceName = currentUserIsOwner || currentUserIsAdmin;
  const canAddRemoveCollaborators = currentUserIsOwner || currentUserIsAdmin; // Simplified for now, can be refined

  useEffect(() => {
    if (workspace?.name) {
      setNewWorkspaceName(workspace.name);
    }
  }, [workspace?.name]);

  const currentMemberRole = members.find(m => m.id === user?.id)?.role;


  const fetchSpaceData = useCallback(async () => {
    if (!accessToken || isAuthLoading || !spaceId) {
      setIsLoading(true);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      // Fetch Workspace Details
      const workspaceResponse = await fetch(`${BACKEND_URL}/workspaces/${spaceId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!workspaceResponse.ok) {
        const errorData = await workspaceResponse.json();
        throw new Error(errorData.detail || "Failed to fetch workspace details");
      }
      const workspaceData: WorkspaceData = await workspaceResponse.json();
      setWorkspace(workspaceData);

      // Fetch Members
      const membersResponse = await fetch(`${BACKEND_URL}/workspaces/${spaceId}/members`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!membersResponse.ok) {
        const errorData = await membersResponse.json();
        throw new Error(errorData.detail || "Failed to fetch workspace members");
      }
      const membersData: {user_id: string, email: string, full_name: string, role: string}[] = await membersResponse.json();
      const mappedMembers = membersData.map(m => ({
        id: m.user_id,
        name: m.full_name,
        email: m.email,
        role: m.role,
      }));
      setMembers(mappedMembers);

      // Fetch Tenders
      const tendersResponse = await fetch(`${BACKEND_URL}/tenders/workspace/${spaceId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!tendersResponse.ok) {
        const errorData = await tendersResponse.json();
        throw new Error(errorData.detail || "Failed to fetch tenders");
      }
      const tendersData: Tender[] = await tendersResponse.json();
      setTenders(tendersData);

    } catch (err: any) {
      setError(err.message || "An unknown error occurred while fetching space data");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, isAuthLoading, spaceId]);

  useEffect(() => {
    fetchSpaceData();
  }, [fetchSpaceData]);

  const handleUpdateWorkspaceName = async () => {
    if (!workspace || !newWorkspaceName.trim() || newWorkspaceName === workspace.name) {
      setIsEditingWorkspaceName(false);
      setNewWorkspaceName(workspace?.name || ""); // Revert to original if no change or invalid
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/workspaces/${workspace.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ name: newWorkspaceName }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to update workspace name");
      }

      await fetchSpaceData(); // Refresh all data to reflect new name and ensure consistency
      setIsEditingWorkspaceName(false);
    } catch (err: any) {
      setError(err.message || "An error occurred while updating workspace name");
      setNewWorkspaceName(workspace?.name || ""); // Revert on error
      setIsEditingWorkspaceName(false);
    }
  };

  const handleCreateTender = async (name: string, files: File[], currentSpaceId: string) => { // Updated to async and receive spaceId
    setIsCreatingTender(true);
    setCreateTenderError(null);
    try {
        // Prepare form data for file upload
        const formData = new FormData();
        formData.append("name", name);
        formData.append("workspace_id", currentSpaceId);
        // Assuming backend expects files individually
        files.forEach((file) => {
            formData.append("files", file); // Backend expects 'files' field for file uploads
        });

        const createTenderResponse = await fetch(`${BACKEND_URL}/tenders/`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${accessToken}`,
                // Do NOT set Content-Type header here; FormData sets it automatically with the correct boundary
            },
            body: formData,
        });

        if (!createTenderResponse.ok) {
            const errorData = await createTenderResponse.json();
            throw new Error(errorData.detail || "Failed to create tender");
        }

        // After successful creation, re-fetch tenders to update the list
        await fetchSpaceData();
        setIsNewTenderOpen(false); // Close dialog on success

    } catch (err: any) {
        setCreateTenderError(err.message || "An unknown error occurred while creating tender");
    } finally {
        setIsCreatingTender(false);
    }
  };

  const handleUpdateMemberRole = async (workspaceId: string, memberId: string, newRole: string) => {
    try {
      let response;
      if (newRole === "NONE") {
        // Remove member
        response = await fetch(`${BACKEND_URL}/workspaces/${workspaceId}/members/${memberId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      } else {
        // Update role
        response = await fetch(`${BACKEND_URL}/workspaces/${workspaceId}/members/${memberId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ role: newRole }),
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to modify member");
      }

      // Re-fetch all space data to update members and potentially currentMemberRole
      await fetchSpaceData();
    } catch (err: any) {
      setError(err.message || "An error occurred while modifying member role");
    }
  };

  const handleAddCollaborator = async () => {
    if (!workspace || !newCollaboratorEmail.trim()) {
      return;
    }
    setAddCollaboratorError(null); // Clear previous errors

    try {
      const response = await fetch(`${BACKEND_URL}/workspaces/${workspace.id}/members`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ user_email: newCollaboratorEmail, role: newCollaboratorRole }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to add collaborator");
      }
      
      await fetchSpaceData(); // Refresh all data to update members
      setShowNewCollaboratorForm(false);
      setNewCollaboratorEmail("");
      setNewCollaboratorRole("VIEWER");
    } catch (err: any) {
      setAddCollaboratorError(err.message || "An error occurred while adding collaborator");
    }
  };

  const handleDeleteTenderClick = (tenderId: string) => {
    setTenderToDeleteId(tenderId);
    setShowDeleteTenderConfirm(true);
  };

  const handleCancelDeleteTender = () => {
    setShowDeleteTenderConfirm(false);
    setTenderToDeleteId(null);
  };

  const handleConfirmDeleteTender = async () => {
    if (!tenderToDeleteId) return;

    try {
      const response = await fetch(`${BACKEND_URL}/tenders/${tenderToDeleteId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to delete tender");
      }

      await fetchSpaceData(); // Refresh the list of tenders
      handleCancelDeleteTender(); // Close dialog and clear ID
    } catch (err: any) {
      setError(err.message || "An error occurred while deleting the tender");
      handleCancelDeleteTender(); // Close dialog anyway
    }
  };

  const handleDownloadDocument = async (tenderId: string, documentId: string, filename: string) => {
    if (!accessToken) {
      setError("Authentication token is missing. Please log in again.");
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/tenders/${tenderId}/documents/${documentId}/download`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to download document: ${response.status} ${response.statusText} - ${errorText}`);
      }

      // Get the content-disposition header to find the actual filename, if provided by backend
      const contentDisposition = response.headers.get("Content-Disposition");
      let downloadFilename = filename;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="([^"]+)"/);
        if (filenameMatch && filenameMatch[1]) {
          downloadFilename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = downloadFilename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || "An error occurred during document download.");
    }
  };

  if (isAuthLoading || isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-background p-6">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </main>
    )
  }

  if (error) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-background p-6">
        <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              {error}
        </div>
        <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
        </Button>
      </main>
    )
  }
  
  // Ensure workspace is not null before rendering its properties
  if (!workspace) {
    return (
        <main className="min-h-screen flex items-center justify-center bg-background p-6">
            <p className="text-muted-foreground">Workspace not found.</p>
        </main>
    );
  }

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-background flex flex-col">
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
                {workspace.name}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Workspace Info */}
        <Card className="border-border rounded-xl bg-card mb-8">
          <CardHeader className="pb-4">
            <div className="flex items-center gap-4">
              <HexagonIcon className="h-8 w-8 text-primary" fill="currentColor" /> {/* Larger HexagonIcon */}
              <div>
                {isEditingWorkspaceName && canEditWorkspaceName ? (
                  <Input
                    value={newWorkspaceName}
                    onChange={(e) => setNewWorkspaceName(e.target.value)}
                    onBlur={handleUpdateWorkspaceName}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleUpdateWorkspaceName();
                      }
                      if (e.key === "Escape") {
                        setIsEditingWorkspaceName(false);
                        setNewWorkspaceName(workspace?.name || "");
                      }
                    }}
                    className="h-9 text-2xl font-semibold bg-background"
                  />
                ) : (
                  <CardTitle 
                    className="text-2xl text-foreground flex items-baseline gap-2 cursor-pointer"
                    onDoubleClick={() => canEditWorkspaceName && setIsEditingWorkspaceName(true)}
                  >
                    {workspace.name}
                    <span className="text-sm text-muted-foreground font-normal ml-auto">
                      Created on {format(new Date(workspace.created_at), "MMMM d, yyyy")}
                    </span>
                  </CardTitle>
                )}
                {workspace.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {workspace.description}
                  </p>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">

            {/* Members Section */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-foreground">
                <Users className="h-4 w-4" />
                <span className="font-medium">
                  Members ({members.length})
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {members.map((member) => {
                  // Determine if current user is owner or admin of this workspace
                  const currentUserIsOwner = members.find(m => m.id === user?.id)?.role === "OWNER";
                  const currentUserIsAdmin = members.find(m => m.id === user?.id)?.role === "ADMIN";
                  
                  // Determine if the role can be edited by the current user
                  let canEditRole = false;
                  if (currentUserIsOwner) {
                    canEditRole = true; // Owner can edit anyone
                  } else if (currentUserIsAdmin) {
                    // Admin can edit non-owner/non-admin members
                    if (member.role !== "OWNER" && member.role !== "ADMIN") {
                      canEditRole = true;
                    }
                  }

                  // Determine if the role selector should be visible (i.e., user is OWNER or ADMIN)
                  const canSeeRoleSelector = currentUserIsOwner || currentUserIsAdmin;

                  return (
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
                      {member.role === "OWNER" ? ( // OWNER role is always plain text, unchangeable via selector
                        <Badge
                          className={`rounded-lg text-xs capitalize ${getRoleColor(member.role)}`}
                        >
                          {member.role}
                        </Badge>
                      ) : canSeeRoleSelector ? (
                        <Select
                          value={member.role}
                          onValueChange={(newRole) => handleUpdateMemberRole(workspace.id, member.id, newRole)}
                          disabled={!canEditRole || isAuthLoading} // Disable if no permission or loading
                        >
                                                  <SelectTrigger className="w-[120px] rounded-lg text-xs">
                                                    <SelectValue>{member.role}</SelectValue>
                                                  </SelectTrigger>
                                                  <SelectContent>
                                                    <SelectItem value="ADMIN">ADMIN</SelectItem>
                                                    <SelectItem value="EDITOR">EDITOR</SelectItem>
                                                    <SelectItem value="VIEWER">VIEWER</SelectItem>
                                                    <SelectItem value="NONE">NONE</SelectItem> {/* Added NONE option */}
                                                  </SelectContent>                        </Select>
                      ) : (
                        <Badge
                          className={`rounded-lg text-xs capitalize ${getRoleColor(member.role)}`}
                        >
                          {member.role}
                        </Badge>
                      )}
                    </div>
                  );
                })}
              </div>
              {canAddRemoveCollaborators && (
                <div className="pt-4">
                  {!showNewCollaboratorForm ? (
                    <Button
                      variant="outline"
                      onClick={() => setShowNewCollaboratorForm(true)}
                      className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent w-full"
                    >
                      <Plus className="mr-2 h-4 w-4" /> Add Collaborator
                    </Button>
                  ) : (
                    <div className="flex flex-col gap-3 p-3 rounded-xl border border-border bg-muted/30">
                      <Input
                        type="email"
                        placeholder="Collaborator Email"
                        value={newCollaboratorEmail}
                        onChange={(e) => setNewCollaboratorEmail(e.target.value)}
                        className="h-9 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
                      />
                      <Select
                        value={newCollaboratorRole}
                        onValueChange={(value) => setNewCollaboratorRole(value)}
                      >
                        <SelectTrigger className="w-full rounded-xl border-border bg-background text-foreground">
                          <SelectValue placeholder="Select Role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ADMIN">ADMIN</SelectItem>
                          <SelectItem value="EDITOR">EDITOR</SelectItem>
                          <SelectItem value="VIEWER">VIEWER</SelectItem>
                        </SelectContent>
                      </Select>
                      <div className="flex gap-2">
                        <Button
                          onClick={handleAddCollaborator}
                          disabled={!newCollaboratorEmail.trim() || isAuthLoading}
                          className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 flex-1"
                        >
                          Add
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowNewCollaboratorForm(false);
                            setNewCollaboratorEmail("");
                            setNewCollaboratorRole("VIEWER");
                            setAddCollaboratorError(null); // Clear error on cancel
                          }}
                          className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent flex-1"
                        >
                          Cancel
                        </Button>
                      </div>
                      {addCollaboratorError && (
                        <p className="text-sm text-destructive mt-2 px-1">
                          {addCollaboratorError}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tenders Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">
              Tenders
            </h2>
            <Button
              onClick={() => {setIsNewTenderOpen(true); setCreateTenderError(null);}}
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
            <div className="space-y-3">
              {tenders.map((tender) => {
                const hasAnalysis = tender.analysis_results && tender.analysis_results.length > 0;
                const finalStatus = hasAnalysis
                  ? tender.analysis_results![tender.analysis_results!.length - 1].status
                  : null;

                return (
                  <div key={tender.id} className="flex items-start gap-2"> {/* Wrapper for Accordion and Delete button */}
                    <Accordion type="single" collapsible className="flex-1">
                      <AccordionItem
                        value={tender.id}
                        className="group border border-border rounded-xl bg-card px-0 overflow-hidden"
                      >
                        <AccordionTrigger className="flex-1 text-left px-6 py-5 hover:no-underline hover:bg-muted/50 [&[data-state=open]]:border-b [&[data-state=open]]:border-border">
                                                  <div className="flex items-center justify-between w-full">
                                                    <div className="flex flex-col items-start text-left">
                                                      <Link 
                                                        href={`/space/${spaceId}/tender/${tender.id}`}
                                                        onClick={(e) => e.stopPropagation()}
                                                        className="text-lg font-medium text-foreground hover:underline"
                                                      >
                                                        {tender.name}
                                                      </Link>
                                                      <span className="text-sm text-muted-foreground mt-1">
                                                        Created {format(new Date(tender.created_at), "MMM d, yyyy")} &middot;{" "}
                                                        {tender.documents?.length || 0} document
                                                        {(tender.documents?.length || 0) !== 1 ? "s" : ""}
                                                      </span>
                                                    </div>
                                                    {finalStatus && (
                                                      <Badge
                                                        className={`rounded-lg ml-4 ${getStatusBadgeClasses(finalStatus)}`}
                                                      >
                                                        {finalStatus.toUpperCase()}
                                                      </Badge>
                                                    )}
                                                  </div>
                                                </AccordionTrigger>
                                                <AccordionContent className="px-6 pb-5 pt-4">
                                                  {(tender.documents?.length || 0) === 0 ? (
                                                    <p className="text-muted-foreground text-sm py-4 text-center">
                                                      No documents uploaded yet
                                                    </p>
                                                  ) : (
                                                    <div className="space-y-2">
                                                      <p className="text-sm font-medium text-muted-foreground mb-3">
                                                        Uploaded Documents
                                                      </p>
                                                      {tender.documents?.map((doc) => (
                                                        <div
                                                          key={doc.id}
                                                          className="flex items-center justify-between p-3 rounded-xl border border-border bg-muted/30 hover:bg-muted/50 cursor-pointer"
                                                          onClick={() => handleDownloadDocument(tender.id, doc.id, doc.filename)}
                                                        >
                                                          <div className="flex items-center gap-3">
                                                            <FileText className="h-5 w-5 text-red-500" />
                                                            <span className="text-sm text-foreground">
                                                              {doc.filename}
                                                            </span>
                                                          </div>
                                                          <span className="text-xs text-muted-foreground">
                                                            {formatFileSize(doc.size)}
                                                          </span>
                                                        </div>
                                                      ))}
                                                    </div>
                                                  )}
                                                </AccordionContent>                      </AccordionItem>
                    </Accordion>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteTenderClick(tender.id)}
                      className={`
                        shrink-0 text-muted-foreground hover:text-destructive mt-5
                        ${(currentMemberRole === "OWNER" || currentMemberRole === "ADMIN") 
                          ? "visible" 
                          : "invisible pointer-events-none"}
                      `}
                    >
                      <Trash2 className="h-5 w-5" />
                    </Button>
                  </div>
                );
              })}
            </div>          )}
        </div>
      </main>

      <NewTenderDialog
        isOpen={isNewTenderOpen}
        onClose={() => setIsNewTenderOpen(false)}
        onSubmit={handleCreateTender}
        spaceId={spaceId} // Pass spaceId
        isSubmitting={isCreatingTender}
        error={createTenderError}
      />

      <DashboardFooter />
      <ChatbotWidget />

      {/* Delete Tender Confirmation Dialog */}
      <AlertDialog open={showDeleteTenderConfirm} onOpenChange={setShowDeleteTenderConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure you want to delete this tender?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              tender and all its associated documents and analysis results.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDeleteTender}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDeleteTender} className="bg-destructive hover:bg-destructive/90">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </ProtectedRoute>
  )
}

