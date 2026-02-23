import { cookies } from "next/headers"
import { NextResponse } from "next/server" // Import NextResponse

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface UserPayload {
  id: string
  email: string
  name: string
  // Add other fields if returned by /users/me endpoint
}

/**
 * Function to set the HttpOnly refresh token cookie.
 */
export function setRefreshTokenCookie(response: NextResponse, token: string) {
  response.cookies.set("refresh_token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production", // Use secure cookies in production
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
}

/**
 * Function to clear the HttpOnly refresh token cookie set by the backend.
 * This is done by setting an expired cookie with the same name.
 */
export function clearRefreshTokenCookie(response: NextResponse) {
  response.cookies.set("refresh_token", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0, // Expire immediately
    path: "/",
  })
}

/**
 * Fetches current user information from the backend.
 * The backend will use the HttpOnly refresh_token cookie to authenticate the request
 * and then provide user details.
 */
export async function getCurrentUser(accessToken: string | null): Promise<UserPayload | null> {
  if (!BACKEND_URL) {
    console.error("Backend URL is not configured for getCurrentUser")
    return null
  }

  if (!accessToken) {
    console.warn("No access token provided for getCurrentUser")
    return null
  }

  try {
    const response = await fetch(`${BACKEND_URL}/users/me`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${accessToken}`,
      },
      // Ensure cookies are sent with this request if it's a server-side fetch
      // For client-side fetch, browser handles it automatically
      cache: 'no-store' // Always get fresh data
    })

    if (!response.ok) {
      console.error(`Failed to fetch current user: ${response.status} ${response.statusText}`)
      // If the token is invalid or expired, the backend will return 401
      // The calling context should handle re-authentication or token refresh
      return null
    }

    const userData = await response.json()
    return {
      id: userData.id,
      email: userData.email,
      name: userData.full_name, // Map backend 'full_name' to frontend 'name'
      // Map other fields as necessary
    } as UserPayload
  } catch (error) {
    console.error("Error fetching current user:", error)
    return null
  }
}


