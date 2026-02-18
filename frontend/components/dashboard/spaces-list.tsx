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
import { Button } from "@/components/ui/button"
import { FileText, ChevronRight, Trash2 } from "lucide-react"
import type { Space } from "@/app/dashboard/page"
import { getStatusBadgeClasses } from "@/lib/style-utils"

interface SpacesListProps {
  spaces: Space[];
  onDeleteSpace: (spaceId: string) => void;
}

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

export function SpacesList({ spaces, onDeleteSpace }: SpacesListProps) {
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
    <div className="space-y-3">
      {spaces.map((space) => (
        <div key={space.id} className="flex items-start gap-2">
          {/* Accordion completamente independiente */}
          <Accordion type="multiple" className="flex-1">
            <AccordionItem
              value={space.id}
              className="group border border-border rounded-xl bg-card px-0 overflow-hidden"
            >
              <AccordionTrigger className="flex-1 text-left px-6 py-5 hover:no-underline hover:bg-muted/50 [&[data-state=open]]:border-b [&[data-state=open]]:border-border">
                <div className="flex items-center gap-4 w-full">
                  <HexagonIcon className="h-6 w-6 text-primary transition-transform duration-300 ease-in-out group-hover:rotate-180" fill="currentColor" />
                  <div className="flex-grow flex flex-col items-start">
                    <div className="flex items-center justify-between w-full gap-2">
                      <Link
                        href={`/space/${space.id}`}
                        className="text-lg font-medium text-foreground hover:text-primary hover:underline transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {space.name}
                      </Link>
                      {space.user_role && (
                        <Badge variant="secondary" className="text-xs font-semibold px-2 py-0.5 rounded-full">
                          {space.user_role}
                        </Badge>
                      )}
                    </div>
                    <span className="text-sm text-muted-foreground mt-1">
                      Created {format(new Date(space.created_at), "MMM d, yyyy")} &middot;{" "}
                      {space.tenders.length} tender{space.tenders.length !== 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              </AccordionTrigger>
              
              <AccordionContent className="px-6 pb-5 pt-4">
                {space.description && (
                  <p className="text-sm text-foreground mb-4 border-b border-border pb-4">
                    {space.description.length > 100
                      ? `${space.description.substring(0, 100)}...`
                      : space.description}
                  </p>
                )}
                {space.tenders.length === 0 ? (
                  <p className="text-muted-foreground text-sm py-2 text-center">
                    No tenders in this space yet
                  </p>
                ) : (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium text-muted-foreground mb-3">
                      Tenders
                    </h4>
                    {space.tenders.map((tender) => {
                      // Determine the status from the last analysis result
                      const hasAnalysis = tender.analysis_results && tender.analysis_results.length > 0;
                      const finalStatus = hasAnalysis
                        ? tender.analysis_results![tender.analysis_results!.length - 1].status
                        : null;

                      return (
                        <Link
                          key={tender.id}
                          href={`/space/${space.id}/tender/${tender.id}`}
                          className="flex items-center justify-between p-4 rounded-xl border border-border hover:bg-muted/50 transition-colors group"
                        >
                          <div className="flex items-center gap-3">
                            <FileText className="h-5 w-5 text-muted-foreground" />
                            <span className="text-foreground font-medium">
                              {tender.name}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            {finalStatus && (
                              <Badge variant="outline" className={`rounded-lg ${getStatusBadgeClasses(finalStatus)}`}>
                                {finalStatus.toUpperCase()}
                              </Badge>
                            )}
                            <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                          </div>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDeleteSpace(space.id)}
            className="shrink-0 text-muted-foreground hover:text-destructive mt-5"
          >
            <Trash2 className="h-5 w-5" />
          </Button>
        </div>
      ))}
    </div>
  )
}