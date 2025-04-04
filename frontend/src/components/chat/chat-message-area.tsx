"use client";

import { useStore } from "@/stores/chat-store";
import { useDeepSearchStore } from "./deep-search/deep-search-service";
import { MessageBubble } from "./message";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "../ui/lib";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

export function ChatMessages({ className }: { className?: string }) {
  const { messages: chatMessages, isLoading } = useStore();
  const { deepSearchMessages, isDeepSearchActive } = useDeepSearchStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  // Determine which messages to display
  const activeMessages = isDeepSearchActive ? deepSearchMessages : chatMessages;

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    if (activeMessages.length > 0) {
      scrollToBottom();
    }
  }, [activeMessages.length]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
    }
  };

  useEffect(() => {
    if (containerRef.current && !isLoading) {
      const { scrollHeight, clientHeight } = containerRef.current;
      const shouldScroll = scrollHeight - clientHeight < 200;
      if (shouldScroll) {
        scrollToBottom();
      }
    }
  }, [activeMessages.length, isLoading]);

  return (
    <div className="relative h-full">
      <div 
        ref={containerRef}
        className={cn("p-4 overflow-y-auto h-full", className)}
        onScroll={handleScroll}
      >
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full mb-4" />
          ))
        ) : (
          <>
            {activeMessages.map((message) => (
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