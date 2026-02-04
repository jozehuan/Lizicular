"use client"

import Link from "next/link"
import { format } from "date-fns"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { FileText, ChevronRight } from "lucide-react"
import type { Space } from "@/app/dashboard/page"

interface SpacesListProps {
  spaces: Space[]
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

export function SpacesList({ spaces }: SpacesListProps) {
  if (spaces.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p className="text-lg">No spaces yet</p>
        <p className="text-sm mt-1">Create your first space to get started</p>
      </div>
    )
  }

  return (
    <Accordion type="multiple" className="space-y-3">
      {spaces.map((space) => (
        <AccordionItem
          key={space.id}
          value={space.id}
          className="border border-border rounded-xl bg-card px-0 overflow-hidden"
        >
          <AccordionTrigger className="px-6 py-5 hover:no-underline hover:bg-muted/50 [&[data-state=open]]:border-b [&[data-state=open]]:border-border">
            <div className="flex flex-col items-start text-left">
              <Link
                href={`/space/${space.id}`}
                className="text-lg font-medium text-foreground hover:text-primary hover:underline transition-colors"
                onClick={(e) => e.stopPropagation()}
              >
                {space.name}
              </Link>
              <span className="text-sm text-muted-foreground mt-1">
                Created {format(space.createdAt, "MMM d, yyyy")} &middot;{" "}
                {space.tenders.length} tender{space.tenders.length !== 1 ? "s" : ""}
              </span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-6 pb-5 pt-4">
            {space.tenders.length === 0 ? (
              <p className="text-muted-foreground text-sm py-2">
                No tenders in this space yet
              </p>
            ) : (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-muted-foreground mb-3">
                  Active Tenders
                </h4>
                {space.tenders.map((tender) => (
                  <Link
                    key={tender.id}
                    href={`/space/${space.id}/tender/${tender.id}`}
                    className="flex items-center justify-between p-4 rounded-xl border border-border hover:bg-muted/50 transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-muted-foreground" />
                      <span className="text-foreground font-medium">
                        {tender.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={`rounded-lg ${getStatusColor(tender.status)}`}>
                        {formatStatus(tender.status)}
                      </Badge>
                      <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
            <div className="mt-4 pt-4 border-t border-border">
              <Link
                href={`/space/${space.id}`}
                className="text-sm font-medium text-foreground hover:underline inline-flex items-center gap-1"
              >
                View all tenders
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
