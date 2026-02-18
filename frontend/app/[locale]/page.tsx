"use client"

import Link from "next/link"
import { useTranslations } from "next-intl"
import { AuthForm } from "@/components/auth/auth-form"
import { FileText, Users, TrendingUp, Sparkles } from "lucide-react"
import { HexagonBackground } from "@/components/ui/hexagon-background"

export default function HomePage() {
  const t = useTranslations("HomePage");
  return (
    <main className="min-h-screen bg-background">
      <section className="relative overflow-hidden py-10 px-6 flex items-center justify-center min-h-[600px]">
        <HexagonBackground />
        <div className="relative z-10 w-full pointer-events-none">
          <AuthForm className="pointer-events-auto" />
        </div>
      </section>

      <section className="py-20 px-6 border-t border-border">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold text-foreground text-center mb-12">
            {t('featuresTitle')}
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <FileText className="h-5 w-5 text-secondary-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                {t('docManagementTitle')}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('docManagementDescription')}
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center mb-4">
                <Users className="h-5 w-5 text-accent-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                {t('collaborationTitle')}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('collaborationDescription')}
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <TrendingUp className="h-5 w-5 text-secondary-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                {t('analysisTitle')}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('analysisDescription')}
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center mb-4">
                <Sparkles className="h-5 w-5 text-accent-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                {t('automationTitle')}
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('automationDescription')}
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="py-8 px-6 border-t border-border font-sans">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            &copy; {new Date().getFullYear()} Lizicular. {t('footerRights')}
          </span>
          <div className="flex items-center gap-6">
            <Link
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('footerPrivacy')}
            </Link>
            <Link
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              {t('footerTerms')}
            </Link>
          </div>
        </div>
      </footer>
    </main>
  )
}

