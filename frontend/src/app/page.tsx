"use client";

import { ChatLayout } from "@/components/chat/chat-layout";
import { useChat } from "@/hooks/use-chat";
import { LoadingScreen } from "@/components/chat/loading-sreen";
export default function ChatPage() {
  const { isLoading, error } = useChat();

  if (error) return <div className="p-4 text-destructive">{error}</div>;
  if (isLoading) return <LoadingScreen />;

  return <ChatLayout />;
}