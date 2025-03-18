/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { api } from "@/lib/api";
import { Message } from "@/types";

type DeepSearchState = {
  isDeepSearchActive: boolean;
  activeDeepSearchChatId: string | null;
  deepSearchMessages: Message[];
  isLoading: boolean;
};

type DeepSearchActions = {
  toggleDeepSearch: (state?: boolean) => void;
  sendDeepSearchMessage: (content: string) => Promise<void>;
  resetDeepSearch: () => void;
};

const initialState: DeepSearchState = {
  isDeepSearchActive: false,
  activeDeepSearchChatId: null,
  deepSearchMessages: [],
  isLoading: false,
};

export const useDeepSearchStore = create<DeepSearchState & DeepSearchActions>()(
  immer((set) => ({
    ...initialState,

    toggleDeepSearch: (state) => {
      set((store) => {
        store.isDeepSearchActive = state ?? !store.isDeepSearchActive;
      });
    },

    // Add optimistic updates for messages
// Update the sendDeepSearchMessage action
sendDeepSearchMessage: async (content) => {
  set({ isLoading: true });
  
  // Add optimistic user message
  const tempUserMessage: Message = {
    id: `temp-user-${Date.now()}`,
    content,
    role: "user",
    created_at: new Date().toISOString(),
    chat_id: "temp-deep-search-chat"
  };

  // Add loading state for assistant
  const tempAssistantMessage: Message = {
    id: `temp-assistant-${Date.now()}`,
    content: "...",
    role: "assistant",
    created_at: new Date().toISOString(),
    chat_id: "temp-deep-search-chat",
    isLoading: true
  };

  set((state) => {
    state.deepSearchMessages = [...state.deepSearchMessages, tempUserMessage, tempAssistantMessage];
  });

  try {
    const { data } = await api.post("/ai/deep-search", { query: content });
    
    // Safely handle response structure
    console.log(data)
    const response = data?.results?.rag_answer || data?.results?.search_summary || {};
    const sources = data?.results?.sources || [];
    
    const ensureStringContent = (response: any): string => {
      try {
        if (typeof response === 'string') return response;
        const content = response?.rag_answer || 
                       response?.search_summary || 
                       JSON.stringify(response, null, 2);
        return String(content)
          .replace(/<think>[\s\S]*?<\/think>/g, '')
          .replace(/\*\*/g, '')
          .trim();
      } catch (e) {
        console.error("Content conversion error:", e);
        return "Could not format response";
      }
    };    const finalContent = ensureStringContent(response);
    
    const finalAssistantMessage: Message = {
      id: data?.message_id || `ai-${Date.now()}`,
      content: finalContent,
      role: "assistant",
      created_at: new Date().toISOString(),
      chat_id: data?.chat_id || "unknown-chat",
      metadata: { sources }
    };

    set((state) => {
      state.deepSearchMessages = state.deepSearchMessages
        .filter(msg => msg.id !== tempAssistantMessage.id)
        .concat(finalAssistantMessage);
      state.activeDeepSearchChatId = data?.chat_id || null;
      state.isLoading = false;
    });

  } catch (error) {
    console.error("Deep search error:", error);
    set((state) => {
      state.deepSearchMessages = state.deepSearchMessages
        .filter(msg => msg.id !== tempUserMessage.id)
        .filter(msg => msg.id !== tempAssistantMessage.id);
      state.isLoading = false;
    });
  }
},


  resetDeepSearch: () => {
      set(initialState);
    },
    
    
  }))
);

