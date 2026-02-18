"use client"

import { cn } from "@/lib/utils"

const Hexagon = ({ className }: { className?: string }) => {
  return (
    <div
      className={cn(
        "w-32 h-36 bg-primary/90 [clip-path:polygon(50%_0%,_100%_25%,_100%_75%,_50%_100%,_0%_75%,_0%_25%)]",
        "transition-transform duration-3000 ease-out hover:duration-3000 hover:rotate-360",
        className
      )}
    />
  )
}

const grid = {
  rows: 8,
  hexagonsPerRow: 12,
}

export const HexagonBackground = () => {
  return (
    <div
      className="absolute inset-0 z-0 overflow-hidden opacity-100"
      aria-hidden="true"
    >
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 scale-130">
        <div className="flex flex-col items-center">
          {Array.from({ length: grid.rows }).map((_, rowIndex) => (
            <div
              key={rowIndex}
              className={cn(
                "flex justify-center gap-16 -mb-2",
                rowIndex % 2 === 1 ? "ml-48" : ""
              )}
            >
              {Array.from({ length: grid.hexagonsPerRow }).map((_, hexIndex) => (
                <Hexagon key={hexIndex} />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
