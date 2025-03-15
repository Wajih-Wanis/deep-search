"use client";

import { useStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "lucide-react";
import { cn } from "../ui/lib";

export function ChatSidebar({ className }: { className?: string }) {
  const { chats, createChat, selectChat, activeChatId } = useStore();

  return (
    <div className={cn("w-64 border-r flex flex-col", className)}>
      <div className="p-4 border-b">
        <Button onClick={createChat} className="w-full">
          <PlusIcon className="mr-2 h-4 w-4" /> New Chat
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-2">
        {chats.map((chat) => (
          <div
            key={chat.id}
            onClick={() => selectChat(chat.id)}
            className={cn(
              "p-2 rounded mb-1 cursor-pointer",
              chat.id === activeChatId
                ? "bg-primary text-primary-foreground"
                : "hover:bg-muted"
            )}
          >
            <div className="truncate">{chat.title}</div>
            <div className="text-xs opacity-75">
              {new Date(chat.created_at).toLocaleDateString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}