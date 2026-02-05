import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 }
      )
    }

    // 1. Call backend /auth/login/json
    const loginResponse = await fetch(`${BACKEND_URL}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    if (!loginResponse.ok) {
      const errorData = await loginResponse.json()
      // Specific backend errors
      if (loginResponse.status === 401) {
        return NextResponse.json(
          { error: "Invalid email or password" },
          { status: 401 }
        )
      }
      return NextResponse.json(
        { error: errorData.detail || "Login failed" },
        { status: loginResponse.status }
      )
    }

    const loginData = await loginResponse.json()
    const accessToken = loginData.access_token // Backend sends access_token

    // 2. Use access_token to get user details from /users/me
    const userMeResponse = await fetch(`${BACKEND_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })

    if (!userMeResponse.ok) {
      const errorData = await userMeResponse.json()
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch user details after login" },
        { status: userMeResponse.status }
      )
    }
    const userMeData = await userMeResponse.json()

    // Create a new NextResponse to allow setting cookies
    const response = NextResponse.json({
      accessToken, // frontend expects camelCase
      user: {
        id: userMeData.id,
        email: userMeData.email,
        name: userMeData.full_name, // Map full_name to name
      },
    })

    // Propagate all Set-Cookie headers from the backend's login response
    const setCookieHeaders = loginResponse.headers.getSetCookie();
    for (const cookieHeader of setCookieHeaders) {
      response.headers.append('Set-Cookie', cookieHeader);
    }

    return response
  } catch (error) {
    console.error("Login API error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
