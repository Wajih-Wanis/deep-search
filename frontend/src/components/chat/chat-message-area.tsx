"use client";

import { useStore } from "@/stores/chat-store";
import { MessageBubble } from "./message";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "../ui/lib";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

export function ChatMessages({ className }: { className?: string }) {
  const { messages, isLoading } = useStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isNearBottom = scrollHeight - scrollTop - clientHeight <= 100;
      if (isNearBottom) {
        scrollToBottom();
      }
    }
  }, [messages]);
  
  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
    }
  };

  return (
    <div className="relative h-full min-h-0">
      <div 
        ref={containerRef}
        className={cn("p-4 overflow-y-auto h-full min-h-0", className)}
        onScroll={handleScroll}
      >
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full mb-4" />
          ))
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
      
      {showScrollButton && (
        <Button
          onClick={scrollToBottom}
          size="icon"
          className="absolute bottom-4 right-4 rounded-full shadow-lg"
        >
          <ChevronDown className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}