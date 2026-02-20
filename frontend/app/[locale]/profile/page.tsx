"use client"

import { useState, useEffect } from "react"
import { useTranslations } from "next-intl"
import { useAuth } from "@/lib/auth-context"
import { useApi } from "@/lib/api"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Loader2, Trash2 } from "lucide-react"
import { toast } from "sonner" // Assuming sonner is the toast library

const AVAILABLE_AVATARS = [
  "/avatar/blue_lizard.png",
  "/avatar/green_lizard.png",
  "/avatar/purple_lizard.png",
  "/avatar/yellow_lizard.png",
]

export default function ProfilePage() {
  const t = useTranslations("ProfilePage")
  const { user, logout, refreshToken } = useAuth()
  const api = useApi()
  const router = useRouter()
  const [name, setName] = useState(user?.name || "")
  const [isUpdating, setIsUpdating] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  useEffect(() => {
    if (user?.name && !name) {
      setName(user.name)
    }
  }, [user?.name, name])

  if (!user) {
    return null
  }

  const handleAvatarSelect = async (avatarPath: string) => {
    if (user.picture === avatarPath) return

    setIsUpdating(true)
    try {
      await api.patch("/users/me", { profile_picture: avatarPath })
      await refreshToken() // Actualizar el estado global del usuario
      toast.success(t("updateSuccess"))
    } catch (error) {
      console.error("Error updating profile picture:", error)
      toast.error(t("updateError"))
    } finally {
      setIsUpdating(false)
    }
  }

  const handleUpdateName = async () => {
    if (!name.trim() || name === user.name) return

    setIsUpdating(true)
    try {
      await api.patch("/users/me", { full_name: name.trim() })
      await refreshToken()
      toast.success(t("updateSuccess"))
    } catch (error) {
      console.error("Error updating name:", error)
      toast.error(t("updateError"))
    } finally {
      setIsUpdating(false)
    }
  }

  const handleDeleteAccount = async () => {
    setIsDeleting(true)
    try {
      await api.delete("/users/me")
      toast.success(t("deleteSuccess"))
      await logout()
      router.push("/")
    } catch (error) {
      console.error("Error deleting account:", error)
      toast.error(t("deleteError"))
      setIsDeleting(false)
    }
  }

  return (
    <div className="min-h-screen bg-background py-10">
      <main className="max-w-4xl mx-auto px-4 sm:px-6">
        <h1 className="text-3xl font-bold mb-8">{t("title")}</h1>

        <div className="grid gap-8">
          {/* Avatar Selection Card */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex flex-col items-center sm:items-start gap-8">
                <div className="relative">
                  <Avatar className="h-24 w-24 sm:h-32 sm:w-32 border-4 border-primary/10 shadow-xl">
                    <AvatarImage src={user.picture || "/avatar/blue_lizard.png"} alt={user.name} />
                    <AvatarFallback className="text-2xl">{user.name.slice(0, 2).toUpperCase()}</AvatarFallback>
                  </Avatar>
                  {isUpdating && (
                    <div className="absolute inset-0 flex items-center justify-center bg-background/50 rounded-full">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full">
                  {AVAILABLE_AVATARS.map((avatar) => (
                    <button
                      key={avatar}
                      onClick={() => handleAvatarSelect(avatar)}
                      disabled={isUpdating}
                      className={`relative aspect-square rounded-xl overflow-hidden border-2 transition-all hover:scale-105 active:scale-95 ${
                        user.picture === avatar
                          ? "border-primary ring-2 ring-primary/20"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <Image
                        src={avatar}
                        alt="Avatar Option"
                        fill
                        className="object-cover"
                      />
                      {user.picture === avatar && (
                        <div className="absolute inset-0 bg-primary/10 flex items-center justify-center">
                          <div className="bg-primary text-primary-foreground rounded-full p-1 shadow-lg">
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              fill="none"
                              viewBox="0 0 24 24"
                              strokeWidth={3}
                              stroke="currentColor"
                              className="w-4 h-4"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* User Info Card */}
          <Card>
            <CardContent className="pt-6 space-y-6">
              <div className="space-y-2">
                <Label htmlFor="full_name" className="text-sm font-medium text-muted-foreground">
                  {t("nameLabel")}
                </Label>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Input
                    id="full_name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={50}
                    disabled={isUpdating}
                    className="flex-1 rounded-xl"
                  />
                  <Button 
                    onClick={handleUpdateName} 
                    disabled={isUpdating || !name.trim() || name === user.name}
                    className="rounded-xl"
                  >
                    {isUpdating && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {t("saveButton")}
                  </Button>
                </div>
              </div>

              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground">Email</p>
                <p className="text-lg px-3 py-2 bg-muted/30 rounded-xl border border-border/50 text-muted-foreground cursor-not-allowed">
                  {user.email}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone Card */}
          <Card className="border-destructive/20 bg-destructive/5">
            <CardContent className="pt-6 space-y-4">
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" className="w-full sm:w-auto shadow-lg shadow-destructive/20">
                    {t("deleteButton")}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{t("deleteConfirmTitle")}</AlertDialogTitle>
                    <AlertDialogDescription>
                      {t("deleteConfirmDescription")}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>{t("deleteCancelAction")}</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDeleteAccount}
                      disabled={isDeleting}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                    >
                      {isDeleting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      {t("deleteConfirmAction")}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
              <p className="text-destructive/80 font-medium text-sm">
                {t("deleteDescription")}
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
