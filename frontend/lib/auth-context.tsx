"use client"

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { useChatbot } from "./chatbot-context"; // Import useChatbot

interface User {
  id: string
  email: string
  name: string
  picture?: string
}

interface AuthContextType {
  user: User | null
  accessToken: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>
  signup: (name: string, email: string, password: string) => Promise<{ success: boolean; error?: string }>
  logout: () => Promise<void>
  refreshToken: () => Promise<boolean>
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
  return null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  // Can't use useChatbot here directly because AuthProvider wraps ChatbotProvider in layout.tsx.
  // We need to inverse the wrapping or handle clearHistory differently.
  // Let's check layout structure first.
  
  // Actually, if ChatbotProvider is inside AuthProvider (as seen in layout.tsx), we cannot consume ChatbotContext here.
  // But we need to clear chatbot history on logout.
  // We can expose a way to register a logout callback or move the state up, but keeping contexts separate is better.
  // A simple solution is to listen to user state changes in ChatbotProvider.

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const csrfToken = getCookie("csrftoken");
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }

      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers,
        credentials: "include",
      })
      
      if (response.ok) {
        const data = await response.json()
        setAccessToken(data.accessToken)
        setUser(data.user)
        return true
      } else {
        return false
      }
    } catch (error) {
      console.error("AuthContext: Error during token refresh fetch:", error)
      return false
    }
  }, [])

  useEffect(() => {
      const initAuth = async () => {
        const success = await refreshToken()
        if (!success) {
          setUser(null)
          setAccessToken(null)
        }
        setIsLoading(false)
      }
      initAuth()
    }, [refreshToken])

  useEffect(() => {
    if (!accessToken) {
      return
    }

    const interval = setInterval(async () => {
      await refreshToken()
    }, 14 * 60 * 1000) // 14 minutes

    return () => {
      clearInterval(interval)
    }
  }, [accessToken, refreshToken])

  const login = async (email: string, password: string) => {
    try {
      const csrfToken = getCookie("csrftoken");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers,
        body: JSON.stringify({ email, password }),
        credentials: "include",
      })

      const data = await response.json()

      if (response.ok) {
        setUser(data.user);
        const refreshSuccess = await refreshToken();
        if (refreshSuccess) {
          return { success: true };
        }
        return { success: false, error: "Login succeeded, but session could not be established." };
      }

      return { success: false, error: data.error || "Login failed" }
    } catch {
      return { success: false, error: "Network error" }
    }
  }

  const signup = async (name: string, email: string, password: string) => {
    try {
      const csrfToken = getCookie("csrftoken");
      const headers: HeadersInit = { "Content-Type": "application/json" };
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }

      const response = await fetch("/api/auth/signup", {
        method: "POST",
        headers,
        body: JSON.stringify({ name, email, password }),
        credentials: "include",
      })

      const data = await response.json()

      if (response.ok) {
        setUser(data.user);
        const refreshSuccess = await refreshToken();
        if (refreshSuccess) {
          return { success: true };
        }
        return { success: false, error: "Signup succeeded, but session could not be established." };
      }

      return { success: false, error: data.error || "Signup failed" }
    } catch {
      return { success: false, error: "Network error" }
    }
  }

  const logout = async () => {
    try {
      const csrfToken = getCookie("csrftoken");
      const headers: HeadersInit = {};
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }

      await fetch("/api/auth/logout", {
        method: "POST",
        headers,
        credentials: "include",
      });
    } catch {
      console.error("AuthContext: Logout API call failed.");
    }
    setUser(null);
    setAccessToken(null);
    router.push("/");
  };

  return (
    <AuthContext.Provider value={{ user, accessToken, isLoading, login, signup, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}