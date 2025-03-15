"use client";

import { useChatUI } from "@/hooks/use-chat-ui";
import { ChatSidebar } from "./chat-sidebar";
import { cn } from "../ui/lib";
import { ChatMessages } from "./chat-message";
import { ChatInput } from "./chat-input";

export function ChatLayout() {
  const { isSidebarOpen } = useChatUI();

  return (
    <div className="flex h-screen overflow-hidden">
      <ChatSidebar className={cn(
        "absolute z-50 lg:relative lg:block transition-transform",
        isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
      )} />
      
      <div className="flex flex-col flex-1 relative">
        <ChatMessages className="flex-1 overflow-auto" />
        <ChatInput className="border-t p-4" />
      </div>
    </div>
  );
}