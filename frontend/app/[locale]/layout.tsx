import React from "react"
import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import { NextIntlClientProvider, useMessages } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { AuthProvider } from '@/lib/auth-context'
import { ChatbotProvider } from "@/lib/chatbot-context"
import { Header } from '@/components/layout/header'
import '../globals.css'

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

export default async function RootLayout({
  children,
  params
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  
  // Obtenemos los mensajes en el servidor
  const messages = await getMessages({ locale });

  return (
    <html lang={locale}>
      <body className={`font-yikes antialiased`}>
        <AuthProvider>
          <NextIntlClientProvider locale={locale} messages={messages}>
            <ChatbotProvider>
              <Header />
              {children}
            </ChatbotProvider>
          </NextIntlClientProvider>
        </AuthProvider>
        <Analytics />
      </body>
    </html>
  )
}
