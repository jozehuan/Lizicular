"use client"

import React from "react"

import { useState, type KeyboardEvent } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { X, Loader2, AlertCircle, Plus } from "lucide-react" // Import Loader2, AlertCircle, and Plus

interface Collaborator {
  email: string;
  role: "ADMIN" | "EDITOR" | "VIEWER";
}

interface CreateSpaceFormProps {
  onSubmit: (name: string, description: string, collaborators: Collaborator[]) => void
  onCancel: () => void
  isSubmitting: boolean
  error: string | null
}

export function CreateSpaceForm({ onSubmit, onCancel, isSubmitting, error }: CreateSpaceFormProps) {
  const [spaceName, setSpaceName] = useState("")
  const [spaceDescription, setSpaceDescription] = useState("")
  const [collaborators, setCollaborators] = useState<Collaborator[]>([])

  const AVAILABLE_ROLES: Collaborator["role"][] = ["ADMIN", "EDITOR", "VIEWER"];

  const handleAddCollaborator = () => {
    setCollaborators([...collaborators, { email: "", role: "VIEWER" }]);
  };

  const handleRemoveCollaborator = (index: number) => {
    setCollaborators(collaborators.filter((_, i) => i !== index));
  };

  const handleCollaboratorEmailChange = (index: number, email: string) => {
    const newCollaborators = [...collaborators];
    newCollaborators[index].email = email;
    setCollaborators(newCollaborators);
  };

  const handleCollaboratorRoleChange = (index: number, role: Collaborator["role"]) => {
    const newCollaborators = [...collaborators];
    newCollaborators[index].role = role;
    setCollaborators(newCollaborators);
  };

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
              maxLength={100}
              className="h-11 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
              disabled={isSubmitting} // Disable when submitting
            />
          </div>

          <div className="space-y-4">
            <Label className="text-foreground block">Collaborators</Label>
            {collaborators.map((collaborator, index) => (
              <div key={index} className="flex items-center gap-2">
                <Input
                  type="email"
                  placeholder="Collaborator Email"
                  value={collaborator.email}
                  onChange={(e) => handleCollaboratorEmailChange(index, e.target.value)}
                  className="flex-1 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
                  disabled={isSubmitting}
                />
                <Select
                  value={collaborator.role}
                  onValueChange={(value: Collaborator["role"]) => handleCollaboratorRoleChange(index, value)}
                  disabled={isSubmitting}
                >
                  <SelectTrigger className="w-[120px] rounded-xl border-border bg-background text-foreground">
                    <SelectValue placeholder="Select Role" />
                  </SelectTrigger>
                  <SelectContent>
                    {AVAILABLE_ROLES.map((role) => (
                      <SelectItem key={role} value={role}>
                        {role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => handleRemoveCollaborator(index)}
                  disabled={isSubmitting}
                  className="rounded-xl border-border text-foreground hover:bg-destructive hover:text-destructive-foreground"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              onClick={handleAddCollaborator}
              disabled={isSubmitting}
              className="mt-2 rounded-xl border-border text-foreground hover:bg-muted"
            >
              <Plus className="mr-2 h-4 w-4" /> Add Collaborator
            </Button>
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
