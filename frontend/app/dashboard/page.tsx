"use client"

import { useState } from "react"
import { DashboardHeader } from "@/components/dashboard/header"
import { DashboardFooter } from "@/components/dashboard/footer"
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget"
import { CreateSpaceForm } from "@/components/dashboard/create-space-form"
import { SpacesList } from "@/components/dashboard/spaces-list"
import { ProtectedRoute } from "@/components/auth/protected-route"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export interface Space {
  id: string
  name: string
  createdAt: Date
  collaborators: string[]
  tenders: Tender[]
}

export interface Tender {
  id: string
  title: string
  status: "draft" | "in-progress" | "analyzed" | "completed"
  files: { name: string; type: string }[]
  createdAt: Date
}

const initialSpaces: Space[] = [
  {
    id: "1",
    name: "Government Infrastructure Projects",
    createdAt: new Date("2024-01-15"),
    collaborators: ["alice@company.com", "bob@company.com"],
    tenders: [
      {
        id: "t1",
        title: "Highway Construction Tender 2024",
        status: "analyzed",
        files: [
          { name: "Technical_Requirements.pdf", type: "pdf" },
          { name: "Budget_Proposal.pdf", type: "pdf" },
        ],
        createdAt: new Date("2024-01-20"),
      },
      {
        id: "t2",
        title: "Bridge Renovation Project",
        status: "in-progress",
        files: [{ name: "Project_Scope.pdf", type: "pdf" }],
        createdAt: new Date("2024-02-01"),
      },
    ],
  },
  {
    id: "2",
    name: "Healthcare Equipment Procurement",
    createdAt: new Date("2024-02-10"),
    collaborators: ["carol@medical.org"],
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
  {
    id: "3",
    name: "IT Services & Software",
    createdAt: new Date("2024-03-01"),
    collaborators: [],
    tenders: [
      {
        id: "t4",
        title: "Cloud Migration Services",
        status: "completed",
        files: [
          { name: "RFP_Document.pdf", type: "pdf" },
          { name: "Vendor_Responses.pdf", type: "pdf" },
          { name: "Evaluation_Matrix.pdf", type: "pdf" },
        ],
        createdAt: new Date("2024-03-05"),
      },
      {
        id: "t5",
        title: "Cybersecurity Assessment",
        status: "in-progress",
        files: [{ name: "Security_Requirements.pdf", type: "pdf" }],
        createdAt: new Date("2024-03-10"),
      },
    ],
  },
]

export default function DashboardPage() {
  const [spaces, setSpaces] = useState<Space[]>(initialSpaces)
  const [showCreateForm, setShowCreateForm] = useState(false)

  const handleCreateSpace = (name: string, collaborators: string[]) => {
    const newSpace: Space = {
      id: Date.now().toString(),
      name,
      createdAt: new Date(),
      collaborators,
      tenders: [],
    }
    setSpaces([newSpace, ...spaces])
    setShowCreateForm(false)
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
            onCancel={() => setShowCreateForm(false)}
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
