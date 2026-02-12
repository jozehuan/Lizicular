import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const { name, email, password } = await request.json()

    if (!name || !email || !password) {
      return NextResponse.json(
        { error: "Name, email and password are required" },
        { status: 400 }
      )
    }

    if (password.length < 6) {
      return NextResponse.json(
        { error: "Password must be at least 6 characters" },
        { status: 400 }
      )
    }

    // 1. Call backend /auth/signup
    const signupResponse = await fetch(`${BACKEND_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: name }),
    })

    if (!signupResponse.ok) {
      const errorData = await signupResponse.json()
      // Specific backend errors
      if (signupResponse.status === 400 && errorData.detail === "Email already registered") {
        return NextResponse.json(
          { error: "Email already registered" },
          { status: 409 } // Conflict
        )
      }
      return NextResponse.json(
        { error: errorData.detail || "Signup failed" },
        { status: signupResponse.status }
      )
    }

    // 2. If signup successful, call backend /auth/login/json to get tokens
    const loginResponse = await fetch(`${BACKEND_URL}/auth/login/json`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    if (!loginResponse.ok) {
      const errorData = await loginResponse.json()
      return NextResponse.json(
        { error: errorData.detail || "Login failed after signup" },
        { status: loginResponse.status }
      )
    }

    const loginData = await loginResponse.json()
    const accessToken = loginData.access_token // Backend sends access_token

    // 3. Use access_token to get user details from /users/me
    const userMeResponse = await fetch(`${BACKEND_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })

    if (!userMeResponse.ok) {
      const errorData = await userMeResponse.json()
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch user details after signup" },
        { status: userMeResponse.status }
      )
    }
    const userMeData = await userMeResponse.json()

    // Create a new NextResponse to allow setting cookies
    const response = NextResponse.json({
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
    console.error("Signup API error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
