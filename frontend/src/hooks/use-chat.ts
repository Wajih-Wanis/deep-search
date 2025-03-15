import { useEffect } from "react";
import { useStore } from "@/stores/chat-store";

export function useChat() {
  const { loadChats, isLoading, error } = useStore();

  useEffect(() => {
    const initialize = async () => {
      try {
        await loadChats();
        // Real time updates to be implemented in this component 
      } catch (err) {
        console.error("Chat initialization error:", err);
      }
    };
    
    initialize();
  }, [loadChats]);

  return { isLoading, error };
}