"use client";

import { useStore } from "@/stores/chat-store";
import { MessageBubble } from "./message";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "../ui/lib";

export function ChatMessages({ className }: { className?: string }) {
  const { messages, isLoading } = useStore();

  return (
    <div className={cn("p-4 overflow-y-auto", className)}>
      {isLoading ? (
        Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full mb-4" />
        ))
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
    </div>
  );
}