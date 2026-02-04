import { NextResponse } from "next/server"
import { clearRefreshTokenCookie } from "@/lib/auth"

export async function POST() {
  try {
    await clearRefreshTokenCookie()
    return NextResponse.json({ success: true })
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    )
  }
}
