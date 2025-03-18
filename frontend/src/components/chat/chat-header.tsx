"use client";

import { useStore } from "@/stores/chat-store";
import { cn } from "../ui/lib";

export function ChatHeader({ className }: { className?: string }) {
  const { activeChatId, chats } = useStore();
  
  const activeChat = chats.find(chat => chat.id === activeChatId);
  const title = activeChat?.title || "New Chat";

  return (
    <div className={cn("p-4", className)}>
      <div className="flex items-center h-12">
        <h1 className="font-semibold text-lg truncate">
          {activeChatId ? title : "New Chat"}
        </h1>
      </div>
    </div>
  );
}

