import { create } from "zustand";

type ChatUIState = {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  error: string | null;
  setError: (error: string | null) => void;
};

export const useChatUI = create<ChatUIState>((set) => ({
  isSidebarOpen: true,
  error: null,
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setError: (error) => set({ error }),
}));