"use client"

import React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { X, Send, MessageCircle, Loader2, Trash2 } from "lucide-react"
import { useApi } from "@/lib/api"

import ReactMarkdown from 'react-markdown';

// Frontend-specific message format
interface DisplayMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
}

// Backend-expected message format
interface ApiMessage {
    role: "user" | "assistant"
    content: string
}

const initialMessages: DisplayMessage[] = [
  {
    id: "welcome",
    content: "Hello! I'm Lizi, your tender management assistant. How can I help you today?",
    role: "assistant",
    timestamp: new Date(),
  },
];

export function ChatbotWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<DisplayMessage[]>(initialMessages)
  const [inputValue, setInputValue] = useState("")
  const [isReplying, setIsReplying] = useState(false) // To track loading state
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const api = useApi();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (isOpen) {
      // A short delay ensures the element is visible before scrolling
      setTimeout(scrollToBottom, 100);
    }
  }, [messages, isOpen])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isReplying) return

    const userMessage: DisplayMessage = {
      id: Date.now().toString(),
      content: inputValue,
      role: "user",
      timestamp: new Date(),
    }

    // Add user message to UI immediately and set loading state
    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsReplying(true)

    try {
        // Map frontend message format to the format expected by the backend
        const messageHistory: ApiMessage[] = [...messages, userMessage].map(msg => ({
            role: msg.role,
            content: msg.content
        }));

        // Call the backend API
        const response = await api.post<{ answer: string }>("/chatbot/chat", {
            messages: messageHistory,
        });

        // Create the agent's response message
        const agentMessage: DisplayMessage = {
            id: (Date.now() + 1).toString(),
            content: response.answer,
            role: "assistant",
            timestamp: new Date(),
        }
        setMessages((prev) => [...prev, agentMessage])

    } catch (error) {
        console.error("Failed to get response from chatbot:", error);
        const errorMessage: DisplayMessage = {
            id: (Date.now() + 1).toString(),
            content: "Sorry, I'm having trouble connecting. Please try again later.",
            role: "assistant",
            timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMessage])
    } finally {
        // Reset loading state
        setIsReplying(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey && !isReplying) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleClearHistory = () => {
    setMessages(initialMessages);
    setInputValue("");
    setIsReplying(false); // Ensure loading state is reset
  };

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
                        <div className="text-sm leading-relaxed prose dark:prose-invert"> {/* Wrapper div */}
                            <ReactMarkdown>
                                {message.content}
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
                        <p className="text-sm leading-relaxed">Lizi is typing...</p>
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
                  placeholder={isReplying ? "Waiting for response..." : "Type your message..."}
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
                  <span className="sr-only">Send message</span>
                </Button>
                <Button
                  onClick={handleClearHistory}
                  size="icon"
                  className="h-10 w-10 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                  disabled={isReplying}
                >
                  <Trash2 className="h-4 w-4" />
                  <span className="sr-only">Delete chat</span>
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
        aria-label={isOpen ? "Close chat" : "Open chat"}
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