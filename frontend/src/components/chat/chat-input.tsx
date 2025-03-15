"use client";

import { useRef } from "react";
import { useStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/components/ui/lib";

export function ChatInput({ className }: { className?: string }) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isLoading } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = textareaRef.current?.value.trim();
    if (!content || isLoading) return;

    await sendMessage(content);
    if (textareaRef.current) textareaRef.current.value = "";
  };

  return (
    <form onSubmit={handleSubmit} className={cn("space-y-4", className)}>
      <div className="relative">
        <Textarea
          ref={textareaRef}
          placeholder="Type your message..."
          className="pr-12 resize-none"
          rows={1}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <Button
          type="submit"
          size="sm"
          className="absolute right-2 bottom-2"
          disabled={isLoading}
        >
          Send
        </Button>
      </div>
    </form>
  );
}