"use client";

import { cn } from "../ui/lib";
import { Card } from "@/components/ui/card";
import { Message } from "@/types";
import { format } from "date-fns";
import { BotIcon, UserIcon } from "lucide-react";
import SyntaxHighlighter from 'react-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

export function MessageBubble({ message }: { message: Message }) {
  
  const isAssistant = message.role === "assistant";
  const isCodeBlock = message.content.startsWith("```");
  const isLoading = message.isLoading ?? false;

  const getValidDate = (dateString?: string | null) => {
    if (!dateString) return new Date();
    
    const parsedDate = new Date(dateString);
    if (!isNaN(parsedDate.getTime())) return parsedDate;
    
    return new Date();
  };

  const formatTime = (date: Date) => {
    try {
      return format(date, "HH:mm");
    } catch (e) {
      console.error("Date formatting error:", e);
      return "00:00";
    }
  };

  const validDate = getValidDate(message.created_at);
  const formattedTime = formatTime(validDate);

  return (
    <div className={cn(
      "flex gap-3 mb-4",
      isAssistant ? "justify-start" : "justify-end"
    )}>
      <div className={cn(
        "flex gap-2 items-start max-w-3xl w-full",
        !isAssistant && "flex-row-reverse"
      )}>
        <div className="mt-1">
          {isAssistant ? (
            <BotIcon className="h-5 w-5 text-primary" />
          ) : (
            <UserIcon className="h-5 w-5 text-muted-foreground" />
          )}
        </div>
        
        <Card className={cn(
          "p-4 overflow-hidden",
          isAssistant 
            ? "bg-muted rounded-tr-none" 
            : "bg-primary text-primary-foreground rounded-tl-none",
          isLoading && "animate-pulse" 
        )}>
 
          <div className="text-sm mb-2 opacity-75">
            {formattedTime}
          </div>
          
          {isLoading ? (
            <div className="flex space-x-1">
              <div className="animate-bounce">.</div>
              <div className="animate-bounce delay-100">.</div>
              <div className="animate-bounce delay-200">.</div>
            </div>
          ) : isCodeBlock ? (
            <SyntaxHighlighter 
              language="typescript"
              style={atomOneDark}
              customStyle={{ background: 'transparent' }}
            >
              {message.content.replace(/```\w*/g, '')}
            </SyntaxHighlighter>
          ) : (
            <div className="whitespace-pre-wrap">{message.content}</div>
          )}

          {message.metadata?.sources && (
            <div className="mt-3 pt-2 border-t text-xs opacity-75">
              Sources:{" "}
              {message.metadata.sources.map((source, index) => (
                <span key={index}>
                  <a
                    href={source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-primary"
                  >
                    {new URL(source).hostname}
                  </a>
                  {index < message.metadata.sources.length - 1 && ", "}
                </span>
              ))}
            </div>
          )}
                  </Card>
      </div>
    </div>
  );
}