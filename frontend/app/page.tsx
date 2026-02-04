import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, FileText, Users, TrendingUp, Sparkles } from "lucide-react"

export default function HomePage() {
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <span className="text-xl font-semibold text-foreground tracking-tight">
            Lizicular
          </span>
          <div className="flex items-center gap-4">
            <Link href="/auth">
              <Button
                variant="outline"
                className="rounded-xl border-border text-foreground hover:bg-muted bg-transparent"
              >
                Sign In
              </Button>
            </Link>
            <Link href="/auth">
              <Button className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="py-24 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-semibold text-foreground leading-tight text-balance">
            Tender Management & Automation Made Simple
          </h1>
          <p className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto text-pretty">
            Streamline your tender process with intelligent automation. Organize workspaces, 
            collaborate with teams, and get AI-powered analysis of your documents.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/auth">
              <Button
                size="lg"
                className="rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-8"
              >
                Start Free Trial
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button
                size="lg"
                variant="outline"
                className="rounded-xl border-border text-foreground hover:bg-muted h-12 px-8 bg-transparent"
              >
                View Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="py-20 px-6 border-t border-border">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-semibold text-foreground text-center mb-12">
            Everything you need to manage tenders efficiently
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <FileText className="h-5 w-5 text-secondary-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                Document Management
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Upload and organize tender documents with ease. Support for PDF and common file formats.
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center mb-4">
                <Users className="h-5 w-5 text-accent-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                Team Collaboration
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Invite collaborators to your workspaces and work together seamlessly on tenders.
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-secondary flex items-center justify-center mb-4">
                <TrendingUp className="h-5 w-5 text-secondary-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                Analysis & Insights
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Get automated analysis of your tender documents with actionable insights.
              </p>
            </div>
            <div className="p-6 rounded-xl border border-border bg-card">
              <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center mb-4">
                <Sparkles className="h-5 w-5 text-accent-foreground" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">
                AI-Powered Automation
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Let AI extract key information and generate summaries from your documents.
              </p>
            </div>
          </div>
        </div>
      </section>

      <footer className="py-8 px-6 border-t border-border">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            &copy; 2024 Lizicular. All rights reserved.
          </span>
          <div className="flex items-center gap-6">
            <Link
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Privacy
            </Link>
            <Link
              href="#"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Terms
            </Link>
          </div>
        </div>
      </footer>
    </main>
  )
}
