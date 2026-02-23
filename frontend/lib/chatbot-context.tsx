"use client"

import React, { createContext, useContext, useState, type ReactNode } from "react"
import { useApi } from "@/lib/api"

export interface DisplayMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
}

interface ApiMessage {
    role: "user" | "assistant"
    content: string
}

interface ChatbotContextType {
  messages: DisplayMessage[]
  isReplying: boolean
  sendMessage: (messageContent: string) => Promise<void>
  clearHistory: () => void
}

const ChatbotContext = createContext<ChatbotContextType | undefined>(undefined)

const initialMessages: DisplayMessage[] = [
  {
    id: "welcome",
    content: "¡Hola! ¿En qué puedo ayudarte?",
    role: "assistant",
    timestamp: new Date(),
  },
];

export function ChatbotProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<DisplayMessage[]>(initialMessages);
  const [isReplying, setIsReplying] = useState(false);
  const api = useApi();

  const sendMessage = async (messageContent: string) => {
    if (!messageContent.trim() || isReplying) return;

    const userMessage: DisplayMessage = {
      id: Date.now().toString(),
      content: messageContent,
      role: "user",
      timestamp: new Date(),
    };

    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setIsReplying(true);

    try {
      const messageHistory: ApiMessage[] = updatedMessages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await api.post<{ answer: string }>("/chatbot/chat", {
        messages: messageHistory,
      });

      const agentMessage: DisplayMessage = {
        id: (Date.now() + 1).toString(),
        content: response.answer,
        role: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Failed to get response from chatbot:", error);
      const errorMessage: DisplayMessage = {
        id: (Date.now() + 1).toString(),
        content: "Sorry, I'm having trouble connecting. Please try again later.",
        role: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsReplying(false);
    }
  };

  const clearHistory = () => {
    setMessages(initialMessages);
    setIsReplying(false);
  };

  return (
    <ChatbotContext.Provider value={{ messages, isReplying, sendMessage, clearHistory }}>
      {children}
    </ChatbotContext.Provider>
  );
}

export function useChatbot() {
  const context = useContext(ChatbotContext);
  if (context === undefined) {
    throw new Error("useChatbot must be used within a ChatbotProvider");
  }
  return context;
}
