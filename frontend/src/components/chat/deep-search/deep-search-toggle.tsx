"use client";

import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useDeepSearchStore } from "./deep-search-service";
import { useStore } from "@/stores/chat-store";

export function DeepSearchToggle() {
  const { activeChatId } = useStore();
  const { isDeepSearchActive, toggleDeepSearch } = useDeepSearchStore();

  if (!activeChatId) return null;

  return (
    <div className="flex items-center gap-2 ml-4">
      <Switch
        id="deep-search-mode"
        checked={isDeepSearchActive}
        onCheckedChange={toggleDeepSearch}
      />
      <Label htmlFor="deep-search-mode" className="text-sm">
        Deep Search
      </Label>
    </div>
  );
}