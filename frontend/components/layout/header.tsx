"use client"

import Link from "next/link"
import Image from "next/image"
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { LogOut } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import { LanguageSwitcher } from "./language-switcher"

export function Header() {
  const t = useTranslations("Header");
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
      <div
        className={
          user
            ? "max-w-7xl mx-auto px-4 sm:px-6 h-16 sm:h-20 flex items-center justify-between"
            : "max-w-5xl mx-auto px-4 sm:px-6 h-16 sm:h-20 flex items-center justify-center"
        }
      >
        <Link href={user ? "/dashboard" : "/"} className="flex items-center gap-2 sm:gap-4">
          <Image
            src="/lizicular.JPG"
            alt="Lizicular Logo"
            width={56}
            height={56}
            className="w-10 h-10 sm:w-20 sm:h-20"
          />
          <span className="relative bottom-1 sm:bottom-2 text-2xl sm:text-4xl font-semibold text-foreground tracking-tight font-yikes">
            Lizicular
          </span>
        </Link>

        {user && (
          <div className="flex items-center gap-2 sm:gap-4">
            <span className="hidden sm:block text-lg font-sans">
              {t('greeting', {name: user.name})}
            </span>
            <Avatar className="h-8 w-8 sm:h-10 sm:w-10 border border-border">
              <AvatarImage src={user.picture || "/placeholder-user.jpg"} alt="User avatar" />
              <AvatarFallback className="bg-secondary text-secondary-foreground text-sm">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <LanguageSwitcher />
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              aria-label={t('signOut')}
              className="h-8 w-8 sm:h-10 sm:w-10"
            >
              <LogOut className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
