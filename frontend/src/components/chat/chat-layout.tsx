"use client";

import { useChatUI } from "@/hooks/use-chat-ui";
import { ChatSidebar } from "./chat-sidebar";
import { cn } from "../ui/lib";
import { ChatMessages } from "./chat-message-area";
import { ChatInput } from "./chat-input";

export function ChatLayout() {
  const { isSidebarOpen } = useChatUI();

  return (
    <div className="flex h-screen overflow-hidden">
      <ChatSidebar className={cn(
        "absolute z-50 lg:relative lg:block transition-transform",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )} />
      
      <div className="flex flex-col flex-1 min-h-0 relative">
        <ChatMessages className="flex-1 overflow-auto min-h-0" />
        <ChatInput className="border-t p-4 shrink-0" />
      </div>
    </div>
  );
}