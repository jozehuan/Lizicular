"use client"

import { useState, useEffect, useCallback } from "react" // Import useEffect
import { DashboardHeader } from "@/components/dashboard/header"
import { DashboardFooter } from "@/components/dashboard/footer"
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget"
import { CreateSpaceForm } from "@/components/dashboard/create-space-form"
import { SpacesList } from "@/components/dashboard/spaces-list"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { Button } from "@/components/ui/button"
import { Plus, Loader2, AlertCircle } from "lucide-react" // Import Loader2 and AlertCircle
import { useAuth } from "@/lib/auth-context" // Import useAuth

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export interface Tender {
  id: string
  name: string // Changed from title to name to match backend
  status?: string // Add status as optional
  created_at: string // Changed from createdAt to created_at
  // Add other fields from TenderSummaryResponse if needed
}

export interface Space {
  id: string
  name: string
  description: string
  owner_id: string
  is_active: boolean
  created_at: string // Changed to string to match backend's datetime
  updated_at: string // Changed to string to match backend's datetime
  user_role: string // Add user_role
  tenders: Tender[]
}

export default function DashboardPage() {
  const { accessToken, isLoading: isAuthLoading } = useAuth()
  const [spaces, setSpaces] = useState<Space[]>([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreatingSpace, setIsCreatingSpace] = useState(false) // New state for creating space
  const [createSpaceError, setCreateSpaceError] = useState<string | null>(null) // New state for create space error

  const fetchSpaces = useCallback(async () => {
    if (!accessToken || isAuthLoading) {
      setIsLoading(true);
      return;
    }
    
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`${BACKEND_URL}/workspaces/detailed/`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to fetch spaces")
      }

      const data: Space[] = await response.json()
      setSpaces(data)
    } catch (err: any) {
      setError(err.message || "An unknown error occurred while fetching spaces")
    } finally {
      setIsLoading(false)
    }
  }, [accessToken, isAuthLoading])

  useEffect(() => {
    fetchSpaces()
  }, [fetchSpaces])

  const handleCreateSpace = async (name: string, description: string, collaborators: string[]) => { // Added description
    setIsCreatingSpace(true)
    setCreateSpaceError(null)
    try {
      // 1. Create the workspace
      const createResponse = await fetch(`${BACKEND_URL}/workspaces/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ name, description }), // Include description
      })

      if (!createResponse.ok) {
        const errorData = await createResponse.json()
        throw new Error(errorData.detail || "Failed to create space")
      }

      const newWorkspace: Space = await createResponse.json()

      // 2. Add collaborators (if any)
      for (const email of collaborators) {
        const addMemberResponse = await fetch(`${BACKEND_URL}/workspaces/${newWorkspace.id}/members`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ user_email: email, role: "VIEWER" }), // Default role VIEWER
        })

        if (!addMemberResponse.ok) {
          const errorData = await addMemberResponse.json()
          console.error(`Failed to add collaborator ${email}:`, errorData.detail)
          // Decide how to handle this error: warn user, rollback, etc.
          // For now, we'll continue trying to add other collaborators and report a general error if any fail.
          setCreateSpaceError(prev => (prev ? `${prev}; Failed to add ${email}` : `Failed to add collaborator ${email}`))
        }
      }

      // Refresh the list of spaces to show the new one and its members
      await fetchSpaces()
      setShowCreateForm(false)
    } catch (err: any) {
      setCreateSpaceError(err.message || "An unknown error occurred while creating space")
    } finally {
      setIsCreatingSpace(false)
    }
  }

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

  return (
    <ProtectedRoute>
    <div className="min-h-screen bg-background flex flex-col">
      <DashboardHeader />
      
      <main className="max-w-4xl mx-auto px-6 py-10 flex-1 w-full">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Your Spaces</h1>
            <p className="text-muted-foreground mt-1">
              Manage your workspaces and tenders
            </p>
          </div>
          <Button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create New Space
          </Button>
        </div>

        {showCreateForm && (
          <CreateSpaceForm
            onSubmit={handleCreateSpace}
            onCancel={() => { setShowCreateForm(false); setCreateSpaceError(null); }} // Clear error on cancel
            isSubmitting={isCreatingSpace}
            error={createSpaceError}
          />
        )}

        <SpacesList spaces={spaces} />
      </main>

      <DashboardFooter />
      <ChatbotWidget />
    </div>
    </ProtectedRoute>
  )
}
