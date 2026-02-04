import { NextResponse } from "next/server"
import { refreshAccessToken } from "@/lib/auth"

export async function POST() {
  try {
    const result = await refreshAccessToken()

    if (!result) {
      return NextResponse.json(
        { error: "Invalid or expired refresh token" },
        { status: 401 }
      )
    }

    return NextResponse.json({
      accessToken: result.accessToken,
      user: result.user,
    })
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
