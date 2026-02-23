"use client";

import { useAuth } from "@/lib/auth-context";
import { ChatbotWidget } from "@/components/dashboard/chatbot-widget";

export function ConditionalChatbot() {
  const { user, isLoading } = useAuth();

  if (isLoading || !user) {
    return null;
  }

  return <ChatbotWidget />;
}
