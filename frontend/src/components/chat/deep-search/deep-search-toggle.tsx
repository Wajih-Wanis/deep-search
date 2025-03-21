"use client";

import { Button } from "@/components/ui/button";
import { useDeepSearchStore } from "./deep-search-service";
import { useStore } from "@/stores/chat-store";
import { Search } from "lucide-react";
import { cn } from "@/components/ui/lib";

export function DeepSearchToggle() {
  const { activeChatId } = useStore();
  const { isDeepSearchActive, toggleDeepSearch } = useDeepSearchStore();

  if (!activeChatId) return null;

  return (
    <Button
      type="button"
      variant={isDeepSearchActive ? "default" : "outline"}
      size="sm"
      className={cn(
        "gap-2 transition-colors min-w-[100px]", 
        isDeepSearchActive 
          ? "bg-primary hover:bg-primary/90" 
          : "bg-background hover:bg-muted"
      )}
      onClick={()=>toggleDeepSearch()}
    >
      <Search className="h-4 w-4" />
      <span>Deep Search</span>
    </Button>
  );
}