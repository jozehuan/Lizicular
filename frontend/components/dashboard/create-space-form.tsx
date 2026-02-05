"use client"

import React from "react"

import { useState, type KeyboardEvent } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X, Loader2, AlertCircle } from "lucide-react" // Import Loader2 and AlertCircle

interface CreateSpaceFormProps {
  onSubmit: (name: string, description: string, collaborators: string[]) => void // Updated signature
  onCancel: () => void
  isSubmitting: boolean // New prop
  error: string | null // New prop
}

export function CreateSpaceForm({ onSubmit, onCancel, isSubmitting, error }: CreateSpaceFormProps) {
  const [spaceName, setSpaceName] = useState("")
  const [spaceDescription, setSpaceDescription] = useState("") // New state for description
  const [collaboratorInput, setCollaboratorInput] = useState("")
  const [collaborators, setCollaborators] = useState<string[]>([])

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && collaboratorInput.trim()) {
      e.preventDefault()
      const email = collaboratorInput.trim().toLowerCase()
      if (email.includes("@") && !collaborators.includes(email)) {
        setCollaborators([...collaborators, email])
        setCollaboratorInput("")
      }
    }
  }

  const removeCollaborator = (email: string) => {
    setCollaborators(collaborators.filter((c) => c !== email))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (spaceName.trim()) {
      onSubmit(spaceName.trim(), spaceDescription.trim(), collaborators) // Pass description
    }
  }

  return (
    <Card className="mb-8 border-border rounded-xl bg-card">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
            {error && ( // Display error message if present
            <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 text-destructive text-sm">
                <AlertCircle className="h-4 w-4 flex-shrink-0" />
                {error}
            </div>
            )}
          <div className="space-y-2">
            <Label htmlFor="space-name" className="text-foreground">Space Name</Label>
            <Input
              id="space-name"
              placeholder="Enter space name"
              value={spaceName}
              onChange={(e) => setSpaceName(e.target.value)}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
              disabled={isSubmitting} // Disable when submitting
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="space-description" className="text-foreground">Space Description (Optional)</Label>
            <Input
              id="space-description"
              placeholder="Enter a brief description for the space"
              value={spaceDescription}
              onChange={(e) => setSpaceDescription(e.target.value)}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
              disabled={isSubmitting} // Disable when submitting
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="collaborators" className="text-foreground">
              Collaborators
              <span className="text-muted-foreground font-normal ml-2 text-sm">
                (Press Enter to add)
              </span>
            </Label>
            <Input
              id="collaborators"
              type="email"
              placeholder="Enter email address"
              value={collaboratorInput}
              onChange={(e) => setCollaboratorInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
              disabled={isSubmitting} // Disable when submitting
            />
            {collaborators.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {collaborators.map((email) => (
                  <Badge
                    key={email}
                    variant="secondary"
                    className="rounded-lg bg-secondary text-secondary-foreground px-3 py-1.5 text-sm"
                  >
                    {email}
                    <button
                      type="button"
                      onClick={() => removeCollaborator(email)}
                      className="ml-2 hover:text-destructive focus:outline-none"
                      aria-label={`Remove ${email}`}
                      disabled={isSubmitting} // Disable when submitting
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              disabled={!spaceName.trim() || isSubmitting} // Disable when submitting or name is empty
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Space"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isSubmitting} // Disable when submitting
              className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent"
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
