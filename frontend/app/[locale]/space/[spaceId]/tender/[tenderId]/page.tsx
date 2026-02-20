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
import { useTranslations } from "next-intl"

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

export default function TenderAnalysisPage({
  params,
}: {
  params: Promise<{ spaceId: string; tenderId: string }>
}) {
    const { spaceId, tenderId } = use(params)
    const t = useTranslations("TenderAnalysisPage");
    const { user, accessToken, isLoading: isAuthLoading } = useAuth()

  const [tenderDetails, setTenderDetails] = useState<Omit<TenderData, 'analysis_results'> | null>(null);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);

  const [workspaceName, setWorkspaceName] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isEditingTenderName, setIsEditingTenderName] = useState(false)
  const [newTenderName, setNewTenderName] = useState("")
  const [currentMemberRole, setCurrentMemberRole] = useState<string | null>(null)

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
  
  // Centralized sequential patching function to avoid rate limits/race conditions
  const patchCompletedResults = async (results: AnalysisResult[]) => {
    const patchedResults: AnalysisResult[] = [];
    for (const result of results) {
      // Force fetch for all completed items to ensure we have the latest full details from the analysis_results collection
      if (result.status === 'completed') {
        try {
          const analysisRes = await fetch(`${API_URL}/analysis-results/${result.id}`, {
            headers: { Authorization: `Bearer ${accessToken}` },
          });
          if (analysisRes.ok) {
            const fullAnalysisData = await analysisRes.json();
            // Merge the fetched data (which might be the flat object or nested)
            // Ideally backend returns the full object. We put it in 'data' prop if our interface expects it,
            // or merge it. Based on previous fixes, we expect 'data' property.
            // Let's assume the endpoint returns the FULL document including 'data' field or the fields themselves.
            // Adjusting based on previous knowledge: The endpoint returns the full document.
            // If the document has a 'data' field, we use it. If it's flat, we might need to adjust.
            // However, the interface AnalysisResult has `data: any`.
            // Let's assume the fetch returns the object that SHOULD go into `data`.
            // Wait, previous backend fix made GET /analysis-results/:id return the full document from analysis_results collection.
            // That document DOES NOT necessarily have a 'data' field wrapping everything if it's dynamic.
            // It has 'info', 'requisitos', etc at top level.
            // But our frontend interface and AnalysisDisplay expect `result.data` to hold this content.
            // So we should assign the whole response to `data`.
            patchedResults.push({ ...result, data: fullAnalysisData });
          } else {
            patchedResults.push(result);
          }
        } catch (patchError) {
          console.error(`Failed to patch analysis data for ${result.id}:`, patchError);
          patchedResults.push(result);
        }
      } else {
        patchedResults.push(result);
      }
    }
    return patchedResults;
  };

  const refreshAnalysisResults = useCallback(async () => {
    if (!accessToken) return;
    try {
      const tenderRes = await fetch(`${API_URL}/tenders/${tenderId}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!tenderRes.ok) return;

      const tenderData: TenderData = await tenderRes.json();
      const results = tenderData.analysis_results || [];
      
      // Use the sequential patcher
      const patchedResults = await patchCompletedResults(results);
      
      setAnalysisResults(patchedResults);
    } catch (e) {
      console.error("Failed to refresh analysis results:", e);
    }
  }, [tenderId, accessToken]);

  const fetchInitialPageData = useCallback(async () => {
    if (!accessToken || !user?.id || isAuthLoading) return;

    setLoading(true);
    setError(null);
    try {
      const [tenderRes, workspaceRes, automationsRes] = await Promise.all([
        fetch(`${API_URL}/tenders/${tenderId}`, { headers: { Authorization: `Bearer ${accessToken}` } }),
        fetch(`${API_URL}/workspaces/${spaceId}`, { headers: { Authorization: `Bearer ${accessToken}` } }),
        fetch(`${API_URL}/automations/`, { headers: { Authorization: `Bearer ${accessToken}` } }),
      ]);

      if (!tenderRes.ok) throw new Error(t('errors.fetchTender'));
      const tenderData: TenderData = await tenderRes.json();
      const { analysis_results: initialResults, ...details } = tenderData;
      setTenderDetails(details);
      setNewTenderName(details.name);
      
      const patchedInitialResults = await patchCompletedResults(initialResults || []);
      setAnalysisResults(patchedInitialResults);

      if (!workspaceRes.ok) throw new Error(t('errors.fetchWorkspace'));
      const workspaceData = await workspaceRes.json();
      setWorkspaceName(workspaceData.name);
      const currentUserMembership = workspaceData.members.find((member: any) => member.user_id === user.id);
      setCurrentMemberRole(currentUserMembership ? currentUserMembership.role : null);

      if (!automationsRes.ok) throw new Error(t('errors.fetchAutomations'));
      const automationsData: Automation[] = await automationsRes.json();
      setAutomations(automationsData);

    } catch (err: any) {
      setError(err.message || t('errors.unexpected'));
    } finally {
      setLoading(false);
    }
  }, [spaceId, tenderId, accessToken, user?.id, isAuthLoading, t]);

  useEffect(() => {
    fetchInitialPageData();
  }, [fetchInitialPageData]);

  useEffect(() => {
    if (analysisResults.length === 0) return;
    const sockets: WebSocket[] = [];
    analysisResults.forEach(result => {
      if (result.status === 'pending' || result.status === 'processing') {
        const wsUrl = API_URL.replace(/^http/, 'ws') + `/ws/analysis/${result.id}`;
        try {
          const ws = new WebSocket(wsUrl);
          ws.onmessage = () => refreshAnalysisResults();
          ws.onerror = (error) => console.error(`WebSocket error for analysis ${result.id}:`, error);
          sockets.push(ws);
        } catch (error) { console.error(`Failed to create WebSocket for analysis ${result.id}:`, error); }
      }
    });
    return () => sockets.forEach(ws => ws.close());
  }, [analysisResults, refreshAnalysisResults]);
  
    useEffect(() => {
      const handleVisibilityChange = () => {
        if (document.visibilityState === 'visible') {
          refreshAnalysisResults(); // Silent background refresh of analysis only
        }
      };
      document.addEventListener('visibilitychange', handleVisibilityChange);
      return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [refreshAnalysisResults]);

  const handleUpdateTenderName = async () => {
    if (!tenderDetails || !accessToken || newTenderName === tenderDetails.name) { setIsEditingTenderName(false); return; }
    try {
      const response = await fetch(`${API_URL}/tenders/${tenderDetails.id}`, {
        method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}`, },
        body: JSON.stringify({ name: newTenderName }),
      });
      if (!response.ok) { throw new Error((await response.json()).detail || t('errors.updateTenderName')); }
      const updatedTender: TenderData = await response.json();
      const { analysis_results, ...details } = updatedTender;
      setTenderDetails(details);
      setIsEditingTenderName(false);
    } catch (err: any) {
      setError(err.message || t('errors.updateTenderName'));
      setNewTenderName(tenderDetails.name);
      setIsEditingTenderName(false);
    }
  };

  const handleDeleteAnalysisClick = (analysisId: string) => setResultToDeleteId(analysisId);

  const handleConfirmDelete = async () => {
    if (!resultToDeleteId || !tenderDetails) return;
    setIsDeleting(true);
    try {
      const response = await fetch(`${API_URL}/tenders/${tenderDetails.id}/analysis/${resultToDeleteId}`, {
        method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) { throw new Error((await response.json()).detail || t('errors.deleteAnalysis')); }
      await refreshAnalysisResults();
    } catch (err: any) { setError(err.message); } finally {
      setIsDeleting(false);
      setResultToDeleteId(null);
    }
  };

  const handleGenerateAnalysis = async () => {
    if (!selectedAutomationId) { setGenerateError(t('errors.selectAutomation')); return; }
    setIsGenerating(true); setGenerateError(null);
    try {
      let finalName = newAnalysisName.trim();
      if (!finalName) {
        const selectedAutomation = automations.find(a => a.id === selectedAutomationId);
        finalName = `${selectedAutomation?.name || "Analysis"} - ${format(new Date(), "yyyy-MM-dd HH:mm")}`;
      }
      const response = await fetch(`${API_URL}/tenders/${tenderId}/generate_analysis`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ automation_id: selectedAutomationId, name: finalName }),
      });
      if (!response.ok) { throw new Error((await response.json()).detail || t('errors.generateAnalysis')); }
      setShowGenerateDialog(false); setNewAnalysisName(""); setSelectedAutomationId(null);
      await refreshAnalysisResults();
    } catch (err: any) { setGenerateError(err.message); } finally { setIsGenerating(false); }
  };

  const [showAddFileDialog, setShowAddFileDialog] = useState(false);
  const [filesToUpload, setFilesToUpload] = useState<File[]>([]);
  const [isUploadingFiles, setIsUploadingFiles] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAddFiles = async () => {
    if (!tenderDetails || filesToUpload.length === 0 || !accessToken) return;
    setIsUploadingFiles(true); setUploadError(null);
    try {
      const formData = new FormData();
      filesToUpload.forEach(file => formData.append("files", file));
      const response = await fetch(`${API_URL}/tenders/${tenderDetails.id}/documents`, {
        method: "POST", headers: { Authorization: `Bearer ${accessToken}` }, body: formData,
      });
      if (!response.ok) { throw new Error((await response.json()).detail || t('errors.uploadFailed')); }
      setShowAddFileDialog(false); setFilesToUpload([]);
      await fetchInitialPageData();
    } catch (err: any) { setUploadError(err.message || t('errors.uploadError')); } finally { setIsUploadingFiles(false); }
  };

  const handleRemoveDocument = async (documentId: string) => {
    if (!tenderDetails || !accessToken) return;
    try {
      const response = await fetch(`${API_URL}/tenders/${tenderDetails.id}/documents/${documentId}`, {
        method: "DELETE", headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) { throw new Error((await response.json()).detail || t('errors.removeDocument')); }
      await fetchInitialPageData();
    } catch (err: any) { setError(err.message || t('errors.removeDocumentError')); }
  };
  
  if (loading) return <div className="flex justify-center items-center min-h-screen"><Loader2 className="h-16 w-16 animate-spin" /></div>;
  if (error) return <div className="flex flex-col justify-center items-center min-h-screen text-red-500"><AlertTriangle className="h-16 w-16 mb-4" /><h1 className="text-2xl font-bold mb-2">{t('errors.fetchTenderTitle')}</h1><p>{error}</p><Link href="/dashboard" className="mt-4 text-blue-500 hover:underline">{t('goToDashboard')}</Link></div>;
  if (!tenderDetails) return <div className="flex flex-col justify-center items-center min-h-screen"><AlertTriangle className="h-16 w-16 mb-4 text-gray-400" /><h1 className="text-2xl font-bold mb-2">{t('notFound.title')}</h1><p>{t('notFound.message')}</p><Link href="/dashboard" className="mt-4 text-blue-500 hover:underline">{t('goToDashboard')}</Link></div>;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <main className="max-w-4xl mx-auto px-6 py-10 flex-1 w-full">
          <Breadcrumb className="mb-8">
            <BreadcrumbList>
              <BreadcrumbItem><BreadcrumbLink href="/dashboard" className="text-muted-foreground hover:text-foreground">{t('breadcrumbs.home')}</BreadcrumbLink></BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem><BreadcrumbLink href={`/space/${spaceId}`} className="text-muted-foreground hover:text-foreground">{workspaceName || spaceId}</BreadcrumbLink></BreadcrumbItem>
              <BreadcrumbSeparator />
              <BreadcrumbItem><BreadcrumbPage className="text-foreground font-medium">{tenderDetails.name}</BreadcrumbPage></BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <Card className="border-border rounded-xl bg-card mb-8">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-grow">
                  {isEditingTenderName && canEditTender ? (
                    <Input value={newTenderName} onChange={(e) => setNewTenderName(e.target.value)} onBlur={handleUpdateTenderName} onKeyDown={(e) => { if (e.key === "Enter") handleUpdateTenderName(); if (e.key === "Escape") { setIsEditingTenderName(false); setNewTenderName(tenderDetails?.name || ""); } }} maxLength={255} className="h-9 text-2xl font-semibold bg-background" />
                  ) : (
                    <CardTitle className="text-2xl text-foreground flex items-baseline gap-2 cursor-pointer" onDoubleClick={() => canEditTender && setIsEditingTenderName(true)}>
                      {tenderDetails.name}
                    </CardTitle>
                  )}
                  <p className="text-muted-foreground mt-2">{t('createdOn', { date: format(new Date(tenderDetails.created_at), "MMMM d, yyyy") })}</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-muted-foreground">{t('attachedFiles')}</h3>
                    {canEditTender && <Button variant="ghost" size="sm" onClick={() => setShowAddFileDialog(true)} className="h-7 px-3 text-muted-foreground hover:text-foreground"><Plus className="h-4 w-4 mr-1" /> {t('addFilesButton')}</Button>}
                  </div>
                  {tenderDetails.documents.length === 0 ? <p className="text-sm text-muted-foreground">{t('noFiles')}</p> : <div className="flex flex-wrap gap-2">{tenderDetails.documents.map((file) => <div key={file.id} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50 border border-border"><FileText className="h-4 w-4 text-red-500" /> <span className="text-sm text-foreground">{file.filename}</span>{canEditTender && <Button variant="ghost" size="icon" onClick={() => handleRemoveDocument(file.id)} className="h-6 w-6 text-muted-foreground hover:text-destructive"><X className="h-4 w-4" /></Button>}</div>)}</div>}
                </div>
                <div className="flex items-center gap-6 pt-2">
                  <div className="flex items-center gap-2"><TrendingUp className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">{t('analysisCount', { count: analysisResults.length })}</span></div>
                  <div className="flex items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" /><span className="text-sm text-muted-foreground">{t('fileCount', { count: tenderDetails.documents.length })}</span></div>
                </div>
              </div>
            </CardContent>
          </Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between"><h2 className="text-xl font-semibold text-foreground">{t('analysisResultsTitle')}</h2>{canEditTender && <Button onClick={() => setShowGenerateDialog(true)}><Plus className="mr-2 h-4 w-4" />{t('generateAnalysisButton')}</Button>}</div>
            <AnalysisDisplay analysisResults={analysisResults} onDelete={handleDeleteAnalysisClick} spaceId={spaceId} tenderId={tenderId}/>
          </div>
        </main>
        <DashboardFooter />
        <ChatbotWidget />
      </div>
      <Dialog open={showAddFileDialog} onOpenChange={setShowAddFileDialog}>
        <DialogContent className="rounded-xl border-border bg-card max-w-lg">
          <DialogHeader>
            <DialogTitle>{t('addFilesDialog.title')}</DialogTitle>
            <DialogDescription>{t('addFilesDialog.description')}</DialogDescription>
          </DialogHeader>
          <div className="space-y-6 pt-4">
            {uploadError && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {uploadError}
              </div>
            )}
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const droppedFiles = Array.from(e.dataTransfer.files).filter((file) => file.type === "application/pdf");
                setFilesToUpload((prev) => [...prev, ...droppedFiles]);
              }}
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors hover:border-primary/50 hover:bg-muted/50"
              aria-disabled={isUploadingFiles}
            >
              <Upload className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
              <p className="text-foreground font-medium">{t('addFilesDialog.dragAndDrop')}</p>
              <p className="text-sm text-muted-foreground mt-1">{t('addFilesDialog.orBrowse')}</p>
              <input ref={fileInputRef} type="file" multiple accept=".pdf" onChange={(e) => { if (e.target.files) { setFilesToUpload((prev) => [...prev, ...Array.from(e.target.files)]); } }} className="hidden" disabled={isUploadingFiles} />
            </div>
            {filesToUpload.length > 0 && (
              <div className="space-y-2">
                <Label className="text-foreground">{t('addFilesDialog.selectedFiles', { count: filesToUpload.length })}</Label>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {filesToUpload.map((file, index) => (
                    <div key={`${file.name}-${index}`} className="flex items-center justify-between p-3 rounded-xl border border-border bg-muted/50">
                      <div className="flex items-center gap-3">
                        <FileText className="h-5 w-5 text-red-500 flex-shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm text-foreground truncate max-w-[250px]">{file.name}</p>
                          <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
                        </div>
                      </div>
                      <button onClick={(e) => { e.stopPropagation(); setFilesToUpload((prev) => prev.filter((_, i) => i !== index)); }} className="text-muted-foreground hover:text-destructive transition-colors p-1" aria-label={`Remove ${file.name}`} disabled={isUploadingFiles}>
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="pt-6">
            <Button variant="outline" onClick={() => { setShowAddFileDialog(false); setFilesToUpload([]); setUploadError(null); }} disabled={isUploadingFiles}>
              {t('addFilesDialog.cancelButton')}
            </Button>
            <Button onClick={handleAddFiles} disabled={filesToUpload.length === 0 || isUploadingFiles}>
              {isUploadingFiles ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />{t('addFilesDialog.uploadingButton')}</>
              ) : (
                t('addFilesDialog.uploadButton')
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
        <DialogContent className="rounded-xl border-border bg-card">
          <DialogHeader>
            <DialogTitle>{t('generateAnalysisDialog.title')}</DialogTitle>
            <DialogDescription>{t('generateAnalysisDialog.description')}</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {generateError && (
               <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                {generateError}
              </div>
            )}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="analysis-name" className="text-right">{t('generateAnalysisDialog.nameLabel')}</Label>
              <Input id="analysis-name" value={newAnalysisName} onChange={(e) => setNewAnalysisName(e.target.value)} placeholder={t('generateAnalysisDialog.namePlaceholder')} maxLength={255} className="col-span-3" />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="automation" className="text-right">{t('generateAnalysisDialog.automationLabel')}</Label>
              <Select onValueChange={setSelectedAutomationId} value={selectedAutomationId || undefined}>
                <SelectTrigger className="col-span-3"><SelectValue placeholder={t('generateAnalysisDialog.automationPlaceholder')} /></SelectTrigger>
                <SelectContent>
                  {automations.map((auto) => (
                    <SelectItem key={auto.id} value={auto.id}>{auto.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowGenerateDialog(false)}>{t('generateAnalysisDialog.cancelButton')}</Button>
            <Button onClick={handleGenerateAnalysis} disabled={!selectedAutomationId || isGenerating}>
              {isGenerating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t('generateAnalysisDialog.generateButton')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

       <AlertDialog open={!!resultToDeleteId} onOpenChange={(open) => !open && setResultToDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t('deleteAnalysisDialog.title')}</AlertDialogTitle>
            <AlertDialogDescription>{t('deleteAnalysisDialog.description')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setResultToDeleteId(null)} disabled={isDeleting}>
              {t('deleteAnalysisDialog.cancelButton')}
            </AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete} disabled={isDeleting} className="bg-destructive hover:bg-destructive/90">
              {isDeleting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              {t('deleteAnalysisDialog.deleteButton')}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </ProtectedRoute>
  )
}
