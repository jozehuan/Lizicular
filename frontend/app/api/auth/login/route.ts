import { NextRequest, NextResponse } from "next/server"
import { generateAccessToken, generateRefreshToken, setRefreshTokenCookie } from "@/lib/auth"

// Mock user database - in production, use a real database
const mockUsers = [
  {
    id: "1",
    email: "demo@lizicular.com",
    password: "demo123",
    name: "Demo User",
  },
  {
    id: "2",
    email: "admin@lizicular.com",
    password: "admin123",
    name: "Admin User",
  },
]

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 }
      )
    }

    // Find user - in production, use database lookup with hashed password comparison
    const user = mockUsers.find(
      (u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password
    )

    if (!user) {
      return NextResponse.json(
        { error: "Invalid email or password" },
        { status: 401 }
      )
    }

    const userPayload = {
      id: user.id,
      email: user.email,
      name: user.name,
    }

    // Generate tokens
    const accessToken = await generateAccessToken(userPayload)
    const refreshToken = await generateRefreshToken(userPayload)

    // Set refresh token in HTTP-only cookie
    await setRefreshTokenCookie(refreshToken)

    return NextResponse.json({
      accessToken,
      user: userPayload,
    })
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
