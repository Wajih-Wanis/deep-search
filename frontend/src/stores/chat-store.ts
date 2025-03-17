/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { api } from "@/lib/api";
import { Chat, Message } from "@/types";

type State = {
  chats: Chat[];
  activeChatId: string | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
};

type Actions = {
  loadChats: () => Promise<void>;
  createChat: () => Promise<void>;
  selectChat: (chatId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
};

export const useStore = create<State & Actions>()(
  immer((set, get) => ({
    chats: [],
    activeChatId: null,
    messages: [],
    isLoading: false,
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
      } catch (error) {
        console.log(error);
        set({ error: "Failed to create chat" });
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
      const { activeChatId } = get();
      if (!activeChatId) return;

      const tempId = `temp-${Date.now()}`;
      const userMessage: Message = {
        id: tempId,
        content,
        role: "user",
        created_at: new Date().toISOString(),
        chat_id: activeChatId
      };

      // Add user message
      set((state) => {
        state.messages.push(userMessage);
      });

      try {
        const { data } = await api.post<{message_id: string, response: string}>("/ai/chat", {
          message: content, 
          chat_id: activeChatId,
        });

        // Add AI response as a new message (don't replace user message)
        set((state) => {
          state.messages.push({
            id: data.message_id || `ai-${Date.now()}`,
            content: data.response,
            role: "assistant",
            created_at: new Date().toISOString(),
            chat_id: activeChatId
          });
        });
      } catch (error) {
        console.log(error);
        set({ error: "Failed to send message" });
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