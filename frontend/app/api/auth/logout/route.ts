import { NextRequest, NextResponse } from "next/server"
import { clearRefreshTokenCookie } from "@/lib/auth"

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    // Manually get the refresh_token from the incoming request's cookies
    const refreshToken = request.cookies.get("refresh_token")?.value
    const accessToken = request.headers.get("Authorization")

    // Call backend /auth/logout, forwarding the token
    const backendLogoutResponse = await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      headers: {
        // Forward both tokens to ensure backend can blacklist them
        ...(refreshToken && { "Cookie": `refresh_token=${refreshToken}` }),
        ...(accessToken && { "Authorization": accessToken }),
      },
    })
    
    // Even if the backend call fails, we proceed to clear the client-side cookie.
    // The primary goal is to log the user out of the frontend.
    if (!backendLogoutResponse.ok) {
        console.warn(`Backend logout failed with status: ${backendLogoutResponse.status}`);
        // We don't block the logout, but this indicates a potential issue,
        // like the backend session not being properly invalidated in Redis.
    }

    // Create a new NextResponse to allow clearing cookies
    const response = NextResponse.json({ success: true })

    // Clear the refresh token cookie from the browser
    clearRefreshTokenCookie(response)

    return response
  } catch (error) {
    console.error("Logout API error:", error)
    // Even in case of a total failure, try to log the user out of the frontend
    const response = NextResponse.json(
      { error: "Internal server error during logout" },
      { status: 500 }
    )
    clearRefreshTokenCookie(response);
    return response;
  }
}
