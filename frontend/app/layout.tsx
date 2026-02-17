import React from "react"
import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { AuthProvider } from '@/lib/auth-context'
import { ChatbotProvider } from "@/lib/chatbot-context"
import { Header } from '@/components/layout/header'
import './globals.css'

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: 'Lizicular - Tender Management & Automation',
  description: 'Modern tender management and automation platform for efficient workspace collaboration',
  generator: 'v0.app',
  icons: {
    icon: '/lizicular.JPG',
    apple: '/apple-icon.png',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-yikes antialiased`}>
        <AuthProvider>
          <ChatbotProvider>
            <Header />
            {children}
          </ChatbotProvider>
        </AuthProvider>
        <Analytics />
      </body>
    </html>
  )
}
