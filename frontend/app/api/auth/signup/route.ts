import { NextRequest, NextResponse } from "next/server"
import { generateAccessToken, generateRefreshToken, setRefreshTokenCookie } from "@/lib/auth"

// Mock user storage - in production, use a real database with bcrypt password hashing
const existingEmails = ["demo@lizicular.com", "admin@lizicular.com"]

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

    // Check if email already exists - in production, check database
    if (existingEmails.includes(email.toLowerCase())) {
      return NextResponse.json(
        { error: "Email already registered" },
        { status: 409 }
      )
    }

    // Create new user - in production, hash password with bcrypt and save to database
    const newUser = {
      id: Date.now().toString(),
      email: email.toLowerCase(),
      name,
    }

    // Generate tokens
    const accessToken = await generateAccessToken(newUser)
    const refreshToken = await generateRefreshToken(newUser)

    // Set refresh token in HTTP-only cookie
    await setRefreshTokenCookie(refreshToken)

    return NextResponse.json({
      accessToken,
      user: newUser,
    })
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
