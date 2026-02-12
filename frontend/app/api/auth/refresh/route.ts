import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: NextRequest) {
  try {
    const refreshToken = request.cookies.get('refresh_token')?.value;

    if (!refreshToken) {
      // If refresh token is not found in cookies, it means the user is not authenticated
      return NextResponse.json({ error: "Refresh token missing" }, { status: 401 });
    }

    // 1. Call backend /auth/refresh with the manually propagated refresh token
    const refreshResponse = await fetch(`${BACKEND_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        'Content-Type': 'application/json', // FastAPI's refresh endpoint expects JSON
        'Cookie': `refresh_token=${refreshToken}`, // Manually set the Cookie header
      },
    });

    if (!refreshResponse.ok) {
      const errorData = await refreshResponse.json()
      return NextResponse.json(
        { error: errorData.detail || "Failed to refresh token" },
        { status: refreshResponse.status }
      )
    }

    const refreshData = await refreshResponse.json()
    const accessToken = refreshData.access_token // Backend sends access_token

    // 2. Use access_token to get user details from /users/me
    const userMeResponse = await fetch(`${BACKEND_URL}/users/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })

    if (!userMeResponse.ok) {
      const errorData = await userMeResponse.json()
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch user details after refreshing token" },
        { status: userMeResponse.status }
      )
    }
    const userMeData = await userMeResponse.json()

    // Create a new NextResponse to propagate the cookies set by the backend
    const response = NextResponse.json({
      accessToken, // frontend expects camelCase
      user: {
        id: userMeData.id,
        email: userMeData.email,
        name: userMeData.full_name, // Map full_name to name
      },
    })
    
    // Propagate all Set-Cookie headers from the backend refresh response
    // The backend /auth/refresh endpoint already sets a new HttpOnly refresh_token cookie.
    // We need to ensure this cookie is passed through to the client.
    const setCookieHeaders = refreshResponse.headers.getSetCookie();
    for (const cookieHeader of setCookieHeaders) {
      response.headers.append('Set-Cookie', cookieHeader);
    }
    
    return response
  } catch (error) {
    console.error("Refresh API error:", error)
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
