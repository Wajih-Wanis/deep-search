"use client";

import { useRef } from "react";
import { useStore } from "@/stores/chat-store";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/components/ui/lib";

export function ChatInput({ className }: { className?: string }) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, isLoading, isGenerating, interruptGeneration } = useStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = textareaRef.current?.value.trim();
    if (!content || isLoading || isGenerating) return;
    if (textareaRef.current) textareaRef.current.value = "";

    await sendMessage(content);
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
          type={isGenerating ? "button" : "submit"}
          size="sm"
          className="absolute right-2 bottom-2"
          disabled={isLoading}
          onClick={isGenerating ? interruptGeneration : undefined}
        >
          {isGenerating ? (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-4 w-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <rect x="5" y="5" width="14" height="14" rx="2" />
            </svg>
          ) : (
            "Send"
          )}
        </Button>
      </div>
    </form>
  );
}