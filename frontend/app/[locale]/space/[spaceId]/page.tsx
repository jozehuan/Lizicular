"use client"

import React from "react"
import { useTranslations } from "next-intl"
import { useState, useEffect, useCallback, useRef, use } from "react"
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
import { FileText, Upload, X, Plus, Users, FolderOpen, Loader2, AlertCircle, Trash2 } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { getStatusBadgeClasses } from "@/lib/style-utils"

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

export interface FrontendTenderDocument {
  id: string;
  filename: string;
  content_type: string;
  size: number;
}

export interface Tender {
  id: string
  name: string
  description?: string
  workspace_id: string
  status: string
  documents?: FrontendTenderDocument[]
  analysis_results?: { status: string }[]
  created_at: string
  updated_at: string
}

export interface Member {
  id: string
  name: string
  email: string
  role: string
  avatar?: string
}

export interface WorkspaceData {
  id: string
  name: string
  description: string
  owner_id: string
  is_active: boolean
  created_at: string
  updated_at: string
}

function getRoleColor(role: string) {
  switch (role.toLowerCase()) {
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
    .filter(Boolean)
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
  spaceId: string
  isSubmitting: boolean
  error: string | null
}

function NewTenderDialog({ isOpen, onClose, onSubmit, spaceId, isSubmitting, error }: NewTenderDialogProps) {
  const t = useTranslations("NewTenderDialog");
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
      onSubmit(tenderName, files, spaceId)
      setTenderName("")
      setFiles([])
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="rounded-xl border-border bg-card max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">{t('title')}</DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {t('description')}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-6 pt-4">
            {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
            </div>
            )}
          <div className="space-y-2">
            <Label htmlFor="tender-name" className="text-foreground">
              {t('nameLabel')}
            </Label>
            <Input
              id="tender-name"
              value={tenderName}
              onChange={(e) => setTenderName(e.target.value)}
              placeholder={t('namePlaceholder')}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
              disabled={isSubmitting}
            />
          </div>

          <div className="space-y-2">
            <Label className="text-foreground">{t('documentsLabel')}</Label>
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
                {t('dragAndDrop')}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {t('orBrowse')}
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
                {t('selectedFiles', {count: files.length})}
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
              {t('cancelButton')}
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!tenderName.trim() || isSubmitting}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('submittingButton')}
                </>
              ) : (
                t('submitButton')
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
  params: Promise<{ spaceId: string }>
}) {
  const { spaceId } = use(params)
  const t = useTranslations("SpaceDetailPage");
  const tDelete = useTranslations("DeleteTenderDialog");
  const tRoles = useTranslations("Roles"); // Added for roles
  const tStatus = useTranslations("Status"); // Added for status
  const { user, accessToken, isLoading: isAuthLoading } = useAuth()
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [tenders, setTenders] = useState<Tender[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isNewTenderOpen, setIsNewTenderOpen] = useState(false)
  const [isCreatingTender, setIsCreatingTender] = useState(false)
  const [createTenderError, setCreateTenderError] = useState<string | null>(null)
  const [showDeleteTenderConfirm, setShowDeleteTenderConfirm] = useState(false)
  const [tenderToDeleteId, setTenderToDeleteId] = useState<string | null>(null)

  const [isEditingWorkspaceName, setIsEditingWorkspaceName] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState(workspace?.name || "");

  const [showNewCollaboratorForm, setShowNewCollaboratorForm] = useState(false);
  const [newCollaboratorEmail, setNewCollaboratorEmail] = useState("");
  const [newCollaboratorRole, setNewCollaboratorRole] = useState("VIEWER");
  const [addCollaboratorError, setAddCollaboratorError] = useState<string | null>(null);

  const currentUserIsOwner = members.find(m => m.id === user?.id)?.role === "OWNER";
  const currentUserIsAdmin = members.find(m => m.id === user?.id)?.role === "ADMIN";
  const canEditWorkspaceName = currentUserIsOwner || currentUserIsAdmin;
  const canAddRemoveCollaborators = currentUserIsOwner || currentUserIsAdmin;

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
      const workspaceResponse = await fetch(`${BACKEND_URL}/workspaces/${spaceId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!workspaceResponse.ok) {
        const errorData = await workspaceResponse.json();
        throw new Error(errorData.detail || t('errors.fetchWorkspace'));
      }
      const workspaceData: WorkspaceData = await workspaceResponse.json();
      setWorkspace(workspaceData);

      const membersResponse = await fetch(`${BACKEND_URL}/workspaces/${spaceId}/members`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!membersResponse.ok) {
        const errorData = await membersResponse.json();
        throw new Error(errorData.detail || t('errors.fetchMembers'));
      }
      const membersData: {user_id: string, email: string, full_name: string, role: string}[] = await membersResponse.json();
      const mappedMembers = membersData.map(m => ({
        id: m.user_id,
        name: m.full_name,
        email: m.email,
        role: m.role,
      }));
      setMembers(mappedMembers);

      const tendersResponse = await fetch(`${BACKEND_URL}/tenders/workspace/${spaceId}`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!tendersResponse.ok) {
        const errorData = await tendersResponse.json();
        throw new Error(errorData.detail || t('errors.fetchTenders'));
      }
      const tendersData: Tender[] = await tendersResponse.json();
      setTenders(tendersData);

    } catch (err: any) {
      setError(err.message || t('errors.unexpected'));
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, isAuthLoading, spaceId, t]);

  useEffect(() => {
    fetchSpaceData();
  }, [fetchSpaceData]);

  const handleUpdateWorkspaceName = async () => {
    if (!workspace || !newWorkspaceName.trim() || newWorkspaceName === workspace.name) {
      setIsEditingWorkspaceName(false);
      setNewWorkspaceName(workspace?.name || "");
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
        throw new Error(errorData.detail || t('errors.updateWorkspace'));
      }

      await fetchSpaceData();
      setIsEditingWorkspaceName(false);
    } catch (err: any) {
      setError(err.message || t('errors.updateWorkspaceUnexpected'));
      setNewWorkspaceName(workspace?.name || "");
      setIsEditingWorkspaceName(false);
    }
  };

  const handleCreateTender = async (name: string, files: File[], currentSpaceId: string) => {
    setIsCreatingTender(true);
    setCreateTenderError(null);
    try {
        const formData = new FormData();
        formData.append("name", name);
        formData.append("workspace_id", currentSpaceId);
        files.forEach((file) => {
            formData.append("files", file);
        });

        const createTenderResponse = await fetch(`${BACKEND_URL}/tenders/`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
            body: formData,
        });

        if (!createTenderResponse.ok) {
            const errorData = await createTenderResponse.json();
            throw new Error(errorData.detail || t('errors.createTender'));
        }

        await fetchSpaceData();
        setIsNewTenderOpen(false);

    } catch (err: any) {
        setCreateTenderError(err.message || t('errors.createTenderUnexpected'));
    } finally {
        setIsCreatingTender(false);
    }
  };

  const handleUpdateMemberRole = async (workspaceId: string, memberId: string, newRole: string) => {
    try {
      let response;
      if (newRole === "NONE") {
        response = await fetch(`${BACKEND_URL}/workspaces/${workspaceId}/members/${memberId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
      } else {
        response = await fetch(`${BACKEND_URL}/workspaces/${workspace.id}/members/${memberId}`, {
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
        throw new Error(errorData.detail || t('errors.modifyMember'));
      }

      await fetchSpaceData();
    } catch (err: any) {
      setError(err.message || t('errors.modifyMemberUnexpected'));
    }
  };

  const handleAddCollaborator = async () => {
    if (!workspace || !newCollaboratorEmail.trim()) {
      return;
    }
    setAddCollaboratorError(null);

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
        throw new Error(errorData.detail || t('errors.addCollaborator'));
      }
      
      await fetchSpaceData();
      setShowNewCollaboratorForm(false);
      setNewCollaboratorEmail("");
      setNewCollaboratorRole("VIEWER");
    } catch (err: any) {
      setAddCollaboratorError(err.message || t('errors.addCollaboratorUnexpected'));
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
        throw new Error(errorData.detail || t('errors.deleteTender'));
      }

      await fetchSpaceData();
      handleCancelDeleteTender();
    } catch (err: any) {
      setError(err.message || t('errors.deleteTenderUnexpected'));
      handleCancelDeleteTender();
    }
  };

  const handleDownloadDocument = async (tenderId: string, documentId: string, filename: string) => {
    if (!accessToken) {
      setError(t('errors.missingToken'));
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
        throw new Error(t('errors.downloadFailed'));
      }

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
      setError(err.message || t('errors.downloadUnexpected'));
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
            {t('retry')}
        </Button>
      </main>
    )
  }
  
  if (!workspace) {
    return (
        <main className="min-h-screen flex items-center justify-center bg-background p-6">
            <p className="text-muted-foreground">{t('workspaceNotFound')}</p>
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
                {t('homeBreadcrumb')}
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
              <HexagonIcon className="h-8 w-8 text-primary" fill="currentColor" />
              <div className="flex-grow">
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
                      {t('createdOn', {date: format(new Date(workspace.created_at), "MMMM d, yyyy")})}
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
                  {t('membersTitle', {count: members.length})}
                </span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {members.map((member) => {
                  let canEditRole = false;
                  if (currentUserIsOwner) {
                    canEditRole = true;
                  } else if (currentUserIsAdmin) {
                    if (member.role !== "OWNER" && member.role !== "ADMIN") {
                      canEditRole = true;
                    }
                  }

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
                      {member.role === "OWNER" ? (
                        <Badge
                          className={`rounded-lg text-xs capitalize ${getRoleColor(member.role)}`}
                        >
                          {tRoles(member.role as "OWNER" | "ADMIN" | "EDITOR" | "VIEWER" | "NONE")}
                        </Badge>
                      ) : canSeeRoleSelector ? (
                        <Select
                          value={member.role}
                          onValueChange={(newRole) => handleUpdateMemberRole(workspace.id, member.id, newRole)}
                          disabled={!canEditRole || isAuthLoading}
                        >
                                                  <SelectTrigger className="w-[120px] rounded-lg text-xs">
                                                    <SelectValue>{tRoles(member.role as "OWNER" | "ADMIN" | "EDITOR" | "VIEWER" | "NONE")}</SelectValue>
                                                  </SelectTrigger>
                                                  <SelectContent>
                                                    <SelectItem value="ADMIN">{tRoles('ADMIN')}</SelectItem>
                                                    <SelectItem value="EDITOR">{tRoles('EDITOR')}</SelectItem>
                                                    <SelectItem value="VIEWER">{tRoles('VIEWER')}</SelectItem>
                                                    <SelectItem value="NONE">{tRoles('NONE')}</SelectItem>
                                                  </SelectContent>                        </Select>
                      ) : (
                        <Badge
                          className={`rounded-lg text-xs capitalize ${getRoleColor(member.role)}`}
                        >
                          {tRoles(member.role as "OWNER" | "ADMIN" | "EDITOR" | "VIEWER" | "NONE")}
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
                      <Plus className="mr-2 h-4 w-4" /> {t('addCollaboratorButton')}
                    </Button>
                  ) : (
                    <div className="flex flex-col gap-3 p-3 rounded-xl border border-border bg-muted/30">
                      <Input
                        type="email"
                        placeholder={t('addCollaboratorEmailPlaceholder')}
                        value={newCollaboratorEmail}
                        onChange={(e) => setNewCollaboratorEmail(e.target.value)}
                        className="h-9 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
                      />
                      <Select
                        value={newCollaboratorRole}
                        onValueChange={(value) => setNewCollaboratorRole(value)}
                      >
                        <SelectTrigger className="w-full rounded-xl border-border bg-background text-foreground">
                          <SelectValue placeholder={t('addCollaboratorRolePlaceholder')} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ADMIN">{tRoles('ADMIN')}</SelectItem>
                          <SelectItem value="EDITOR">{tRoles('EDITOR')}</SelectItem>
                          <SelectItem value="VIEWER">{tRoles('VIEWER')}</SelectItem>
                        </SelectContent>
                      </Select>
                      <div className="flex gap-2">
                        <Button
                          onClick={handleAddCollaborator}
                          disabled={!newCollaboratorEmail.trim() || isAuthLoading}
                          className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 flex-1"
                        >
                          {t('addCollaboratorAddButton')}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setShowNewCollaboratorForm(false);
                            setNewCollaboratorEmail("");
                            setNewCollaboratorRole("VIEWER");
                            setAddCollaboratorError(null);
                          }}
                          className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent flex-1"
                        >
                          {t('addCollaboratorCancelButton')}
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
              {t('tendersTitle')}
            </h2>
            <Button
              onClick={() => {setIsNewTenderOpen(true); setCreateTenderError(null);}}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              <Plus className="mr-2 h-4 w-4" />
              {t('newTenderButton')}
            </Button>
          </div>

          {tenders.length === 0 ? (
            <Card className="border-border rounded-xl bg-card">
              <CardContent className="py-16 text-center">
                <FolderOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
                <p className="text-lg text-muted-foreground">{t('noTendersTitle')}</p>
                <p className="text-sm text-muted-foreground mt-1">
                  {t('noTendersSubtitle')}
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
                const statusKey = finalStatus?.toLowerCase(); // Get the raw status key

                return (
                  <div key={tender.id} className="flex items-start gap-2">
                    <Accordion type="single" collapsible className="flex-1">
                      <AccordionItem
                        value={tender.id}
                        className="group border border-border rounded-xl bg-card px-0 overflow-hidden shadow-sm"
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
                                                        {t('createdOn', {date: format(new Date(tender.created_at), "MMMM d, yyyy")})} &middot;{" "}
                                                        {t('documentsCount', {count: tender.documents?.length || 0})}
                                                      </span>
                                                    </div>
                                                    {finalStatus && (
                                                      <Badge
                                                        className={`rounded-lg ml-4 ${getStatusBadgeClasses(finalStatus)}`}
                                                      >
                                                        {tStatus(statusKey) || finalStatus.toUpperCase()}
                                                      </Badge>
                                                    )}
                                                  </div>
                                                </AccordionTrigger>
                                                <AccordionContent className="px-6 pb-5 pt-4">
                                                  {(tender.documents?.length || 0) === 0 ? (
                                                    <p className="text-muted-foreground text-sm py-4 text-center">
                                                      {t('noDocumentsUploaded')}
                                                    </p>
                                                  ) : (
                                                    <div className="space-y-2">
                                                      <p className="text-sm font-medium text-muted-foreground mb-3">
                                                        {t('uploadedDocuments')}
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
        spaceId={spaceId}
        isSubmitting={isCreatingTender}
        error={createTenderError}
      />

      <DashboardFooter />
      <ChatbotWidget />

      {/* Delete Tender Confirmation Dialog */}
      <AlertDialog open={showDeleteTenderConfirm} onOpenChange={setShowDeleteTenderConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{tDelete('title')}</AlertDialogTitle>
            <AlertDialogDescription>
              {tDelete('description')}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancelDeleteTender}>{tDelete('cancelButton')}</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDeleteTender} className="bg-destructive hover:bg-destructive/90">
              {tDelete('confirmButton')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
    </ProtectedRoute>
  )
}
