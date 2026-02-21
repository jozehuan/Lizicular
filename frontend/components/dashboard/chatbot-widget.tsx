"use client"

import React, { useState, useRef, useEffect } from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { X, Send, MessageCircle, Loader2, Trash2 } from "lucide-react"
import { useChatbot } from "@/lib/chatbot-context"
import { useAuth } from "@/lib/auth-context"
import ReactMarkdown from 'react-markdown'

export function ChatbotWidget() {
  const t = useTranslations("ChatbotWidget");
  const [isOpen, setIsOpen] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const { messages, isReplying, sendMessage, clearHistory } = useChatbot()
  const { user } = useAuth()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (isOpen) {
      setTimeout(scrollToBottom, 100);
    }
  }, [messages, isOpen])

  const handleSendMessage = () => {
    sendMessage(inputValue);
    setInputValue(""); // Clear input after sending
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isReplying) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  if (!user) return null

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {isOpen && (
        <Card className="absolute bottom-16 right-0 w-80 sm:w-96 rounded-xl border-border bg-card shadow-xl overflow-hidden flex flex-col">
          <CardContent className="p-0 flex-1 flex flex-col">
            <div className="h-100 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl px-4 py-2.5 ${
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-foreground"
                    }`}
                  >
                    {message.role === "user" ? (
                        <p className="text-sm leading-relaxed">{message.content}</p>
                    ) : (
                        <div className="text-sm leading-relaxed prose dark:prose-invert prose-ul:list-disc prose-ul:pl-4 prose-ol:list-decimal prose-ol:pl-4"> 
                            <ReactMarkdown>
                                {message.content.replace(/\\n/g, '\n')}
                            </ReactMarkdown>
                        </div>
                    )}
                  </div>
                </div>
              ))}
               {isReplying && (
                <div className="flex justify-start">
                    <div className="max-w-[80%] rounded-xl px-4 py-2.5 bg-muted text-foreground flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin"/>
                        <p className="text-sm leading-relaxed">{t('typing')}</p>
                    </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            <div className="border-t border-border p-4">
              <div className="flex items-center gap-2">
                <Input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={isReplying ? t('waiting') : t('placeholder')}
                  className="flex-1 h-10 rounded-xl border-border bg-background text-foreground placeholder:text-muted-foreground"
                  disabled={isReplying}
                />
                <Button
                  onClick={handleSendMessage}
                  size="icon"
                  className="h-10 w-10 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                  disabled={!inputValue.trim() || isReplying}
                >
                  <Send className="h-4 w-4" />
                  <span className="sr-only">{t('sendAria')}</span>
                </Button>
                <Button
                  onClick={clearHistory}
                  size="icon"
                  className="h-10 w-10 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                  disabled={isReplying}
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">{t('deleteAria')}</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Button
        onClick={() => setIsOpen(!isOpen)}
        size="icon"
        className="h-14 w-14 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 shadow-lg"
        aria-label={isOpen ? t('closeAria') : t('openAria')}
      >
        {isOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <MessageCircle className="h-7 w-7" />
        )}
      </Button>
    </div>
  )
}