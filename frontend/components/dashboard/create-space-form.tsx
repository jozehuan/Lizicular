"use client"

import React from "react"

import { useState, type KeyboardEvent } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

interface CreateSpaceFormProps {
  onSubmit: (name: string, collaborators: string[]) => void
  onCancel: () => void
}

export function CreateSpaceForm({ onSubmit, onCancel }: CreateSpaceFormProps) {
  const [spaceName, setSpaceName] = useState("")
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
      onSubmit(spaceName.trim(), collaborators)
    }
  }

  return (
    <Card className="mb-8 border-border rounded-xl bg-card">
      <CardContent className="p-6">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="space-name" className="text-foreground">Space Name</Label>
            <Input
              id="space-name"
              placeholder="Enter space name"
              value={spaceName}
              onChange={(e) => setSpaceName(e.target.value)}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
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
              disabled={!spaceName.trim()}
              className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
            >
              Save Space
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
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
