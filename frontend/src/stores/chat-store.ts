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

export const useStore = create<State & Actions>()(immer((set, get) => ({
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
    } catch (error) {
        console.log(error)
      set({ error: "Failed to load chats", isLoading: false });
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
        console.log(error)
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
        console.log(error)
      set({ error: "Failed to load messages", isLoading: false });
    }
  },

  sendMessage: async (content) => {
    const { activeChatId } = get();
    if (!activeChatId) return;

    const tempId = `temp-${Date.now()}`;
    const newMessage: Message = {
        id: tempId,
        content,
        role: "user",
        created_at: new Date().toISOString(),
        chat_id: ""
    };

    // Optimistic update
    set((state) => {
      state.messages.push(newMessage);
    });

    try {
      const { data } = await api.post("/ai/chat", {
        message: content,
        chat_id: activeChatId,
      });

      set((state) => {
        const index = state.messages.findIndex((m: { id: string; }) => m.id === tempId);
        if (index > -1) {
          state.messages[index] = {
            ...data,
            id: data.message_id,
            content: data.response,
            role: "assistant",
            createdAt: new Date().toISOString(),
          };
        }
      });
    } catch (error) {
        console.log(error)
      set((state) => {
        state.messages = state.messages.filter((m: { id: string; }) => m.id !== tempId);
        state.error = "Failed to send message";
      });
    }
  },

  deleteChat: async (chatId) => {
    try {
      await api.delete(`/chats/${chatId}`);
      set((state) => {
        state.chats = state.chats.filter((c: { id: string; }) => c.id !== chatId);
        if (state.activeChatId === chatId) {
          state.activeChatId = null;
          state.messages = [];
        }
      });
    } catch (error) {
        console.log(error)
      set({ error: "Failed to delete chat" });
    }
  },
})));