"use client";

import { useStore } from "@/stores/chat-store";
import { DeepSearchToggle } from "./deep-search/deep-search-toggle";

export function ChatHeader() {
  const { activeChatId, chats } = useStore();
  
  const activeChat = chats.find(chat => chat.id === activeChatId);
  const title = activeChat?.title || "New Chat";

  return (
    <div className="p-4 border-b" >
      <div className="flex items-center h-12">
        <h1 className="font-semibold text-lg truncate">
          {activeChatId ? title : "New Chat"}
        </h1>
        <DeepSearchToggle />
      </div>
    </div>
  );
}

