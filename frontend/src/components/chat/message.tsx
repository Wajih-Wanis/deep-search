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
  const isLoading = message.isLoading;
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
            {format(new Date(message.created_at || Date.now()), "HH:mm")}
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
              Sources: {message.metadata.sources.join(', ')}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}