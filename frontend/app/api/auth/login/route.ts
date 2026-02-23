import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

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
      let errorData = { detail: "Login failed" };
      try {
        errorData = await loginResponse.json();
      } catch (e) {
        // Backend returned a non-JSON response
        console.error("Failed to parse login error response:", await loginResponse.text());
      }

      if (loginResponse.status === 401) {
        return NextResponse.json(
          { error: "Invalid email or password" },
          { status: 401 }
        );
      }
      return NextResponse.json(
        { error: errorData.detail || "An unexpected error occurred" },
        { status: loginResponse.status }
      );
    }

    const loginData = await loginResponse.json();
    const accessToken = loginData.access_token; // Backend sends access_token

    if (!accessToken) {
      console.error("Backend login response missing access_token");
      return NextResponse.json(
        { error: "Login failed: invalid server response" },
        { status: 500 }
      );
    }

    // 2. Use access_token to get user details from /users/me
    const userMeResponse = await fetch(`${BACKEND_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });

    if (!userMeResponse.ok) {
      let errorData = { detail: "Failed to fetch user details after login" };
      try {
        errorData = await userMeResponse.json();
      } catch (e) {
        console.error("Failed to parse user details error response:", await userMeResponse.text());
      }
      return NextResponse.json(
        { error: errorData.detail },
        { status: userMeResponse.status }
      );
    }
    const userMeData = await userMeResponse.json()

    // Create a new NextResponse to allow setting cookies
    const response = NextResponse.json({
      user: {
        id: userMeData.id,
        email: userMeData.email,
        name: userMeData.full_name, // Map full_name to name
        picture: userMeData.profile_picture,
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
