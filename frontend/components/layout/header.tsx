"use client"

import Link from "next/link"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth-context"

export function Header() {
  const { user, logout } = useAuth()
  const router = useRouter()

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2)
  }

  const handleLogout = async () => {
    router.push("/")
    await logout()
  }

  return (
    <header className="border-b border-border bg-card">
      <div className={user ? "max-w-7xl mx-auto h-20 flex items-center justify-between" : "max-w-5xl mx-auto px-6 h-20 flex items-center justify-center"}>
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-4">
          <Image src="/lizicular.JPG" alt="Lizicular Logo" width={56} height={56} />
          <span className="text-4xl font-semibold text-foreground tracking-tight font-yikes">
            Lizicular
          </span>
        </Link>

        {user && (
          <div className="flex items-center gap-4">
            <span className="text-lg font-sans">Hola, {user.name}!</span>
            <Avatar className="h-10 w-10 border border-border">
              <AvatarImage src={user.picture || "/placeholder-user.jpg"} alt="User avatar" />
              <AvatarFallback className="bg-secondary text-secondary-foreground">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <Button variant="ghost" size="icon" onClick={handleLogout} aria-label="Sign Out">
              <LogOut className="h-5 w-5 text-muted-foreground" />
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
