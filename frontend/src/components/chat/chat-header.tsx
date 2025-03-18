"use client";

import { useStore } from "@/stores/chat-store";

export function ChatHeader() {
  const { activeChatId, chats } = useStore();
  
  const activeChat = chats.find(chat => chat.id === activeChatId);
  const title = activeChat?.title || "New Chat";

  return (
    <div className="border-b p-4">
      <div className="flex items-center h-12">
        <h1 className="font-semibold text-lg truncate">
          {activeChatId ? title : "New Chat"}
        </h1>
      </div>
    </div>
  );
}

