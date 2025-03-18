"use client";

import { useChatUI } from "@/hooks/use-chat-ui";
import { ChatSidebar } from "./chat-sidebar";
import { cn } from "../ui/lib";
import { ChatMessages } from "./chat-message-area";
import { ChatInput } from "./chat-input";
import { ChatHeader } from "./chat-header";

export function ChatLayout() {
  const { isSidebarOpen } = useChatUI();

  return (
    <div className="flex h-screen flex-col overflow-hidden">
    <ChatHeader className="shrink-0 border-b" /> 
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ChatSidebar className={cn(
          "absolute z-50 lg:relative lg:block transition-transform h-full",
          isSidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )} />
        
        <div className="flex flex-col flex-1 min-h-0">
          <ChatMessages className="flex-1 overflow-auto" />
          <div className="shrink-0 border-t">
            <ChatInput className="p-4 bg-background" />
          </div>
        </div>
      </div>
    </div>
  );
}