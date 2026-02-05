import { NextResponse } from "next/server"
import { clearRefreshTokenCookie } from "@/lib/auth"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST() {
  try {
    // Call backend /auth/logout
    // The refresh token cookie will be sent automatically
    const backendLogoutResponse = await fetch(`${BACKEND_URL}/auth/logout`, {
      method: "POST",
      credentials: "include", // Ensure cookies are sent
    })

    // Create a new NextResponse to allow clearing cookies
    const response = NextResponse.json({ success: true })

    // Clear the refresh token cookie from the frontend's side using the updated function
    clearRefreshTokenCookie(response)
    
    // Check if the backend also tried to clear its cookie and propagate it if necessary
    // This is more of a defensive measure; ideally, the above clearRefreshTokenCookie should suffice for the frontend.
    const setCookieHeader = backendLogoutResponse.headers.get("set-cookie");
    if (setCookieHeader) {
      response.headers.append("set-cookie", setCookieHeader);
    }

    return response
  } catch (error) {
    console.error("Logout API error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
