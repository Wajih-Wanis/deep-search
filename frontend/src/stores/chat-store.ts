/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { api } from "@/lib/api";
import { Chat, Message } from "@/types";
import axios, { CancelTokenSource } from "axios";
import { useDeepSearchStore } from "@/components/chat/deep-search/deep-search-service";

type State = {
  chats: Chat[];
  activeChatId: string | null;
  messages: Message[];
  isLoading: boolean;
  isGenerating: boolean;
  cancelTokenSource : CancelTokenSource | null ;
  error: string | null;
};

type Actions = {
  loadChats: () => Promise<void>;
  createChat: () => Promise<string | null>;
  selectChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  interruptGeneration: () => void;
};

export const useStore = create<State & Actions>()(
  immer((set, get) => ({
    chats: [],
    activeChatId: null,
    messages: [],
    isLoading: false,
    isGenerating: false,
    cancelTokenSource: null,
    error: null,

    loadChats: async () => {
      set({ isLoading: true, error: null });
      try {
        const { data } = await api.get<Chat[]>("/chats");
        set({ chats: data, isLoading: false });
      } catch (error: any) {
        console.error("Chat load error:", error);
        set({ 
          error: error.response?.data?.message || "Failed to load chats",
          isLoading: false
        });
      }
    },

    createChat: async () => {
      try {
        const { data } = await api.post<Chat>("/chats");
        set((state) => {
          state.chats.unshift(data);
          state.activeChatId = data.id;
          state.messages = [];
        });
        return data.id; // Return the new chat ID
      } catch (error) {
        console.log(error);
        set({ error: "Failed to create chat" });
        return null;
      }
    },
    selectChat: async (chatId) => {
      if (get().activeChatId === chatId) return;
      
      set({ isLoading: true, activeChatId: chatId });
      try {
        const { data } = await api.get<Message[]>(`/chats/${chatId}/messages`);
        set({ messages: data, isLoading: false });
      } catch (error) {
        console.log(error);
        set({ error: "Failed to load messages", isLoading: false });
      }
    },

    sendMessage: async (content) => {

      const {isDeepSearchActive, sendDeepSearchMessage } = useDeepSearchStore.getState();

      if (isDeepSearchActive) {
        await sendDeepSearchMessage(content);
        return;
      }


      if (get().isGenerating) return;

      let targetChatId = get().activeChatId;
      if (!targetChatId) {
        targetChatId = await get().createChat();
        if (!targetChatId) return;
      }

      const source = axios.CancelToken.source();
      set({cancelTokenSource: source, isGenerating: true});
      
     

      const tempId = `temp-${Date.now()}`;
      const userMessage: Message = {
        id: tempId,
        content,
        role: "user",
        created_at: new Date().toISOString(),
        chat_id: targetChatId,
      };

      const loadingMessage: Message = {
        id : `loading-${Date.now()}`,
        content: "...",
        role: "assistant",
        created_at: new Date().toISOString(),
        chat_id: targetChatId,
        isLoading: true
      }


      // Add user message
      set((state) => {
        state.messages.push(userMessage, loadingMessage);
      });

      try {
        const { data } = await api.post<{message_id: string, response: string}>("/ai/chat", {
          message: content, 
          chat_id: targetChatId,
        },
      { cancelToken: source.token});

        // Add AI response as a new message (don't replace user message)
        set((state) => {
          // Replace loading message
          const index = state.messages.findIndex(m => m.isLoading);
          if (index !== -1) {
            state.messages[index] = {
              id: data.message_id || `ai-${Date.now()}`,
              content: data.response,
              role: "assistant",
              created_at: new Date().toISOString(),
              chat_id: targetChatId
            };
          }
          state.isGenerating = false;
          state.cancelTokenSource = null;
        });
      } catch (error) {
        if (axios.isCancel(error)) {
          console.log("Request canceled");
        } else {
          console.log(error);
          set({ error: "Failed to send message" });
        }
        // Remove loading message on error/cancel
        set((state) => {
          state.messages = state.messages.filter(m => !m.isLoading);
          state.isGenerating = false;
          state.cancelTokenSource = null;
        });
      }
    },

    interruptGeneration: () => {
      const { cancelTokenSource } = get();
      if (cancelTokenSource) {
        cancelTokenSource.cancel("User interrupted generation");
        set({
          isGenerating: false,
          cancelTokenSource: null,
          messages: get().messages.filter(m => !m.isLoading)
        });
      }
    },

    deleteChat: async (chatId) => {
      try {
        await api.delete(`/chats/${chatId}`);
        set((state) => {
          state.chats = state.chats.filter((c) => c.id !== chatId);
          if (state.activeChatId === chatId) {
            state.activeChatId = null;
            state.messages = [];
          }
        });
      } catch (error) {
        console.log(error);
        set({ error: "Failed to delete chat" });
      }
    },
  }))
);