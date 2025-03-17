export interface Chat {
    id: string;
    title: string;
    is_deep_search: boolean;
    created_at: string;
    updated_at: string;
    user_id: string;
  }
  
  export interface Message {
    id: string;
    content: string;
    role: "user" | "assistant";
    created_at: string;
    chat_id: string;
    isLoading?: boolean;
    metadata?: {
      sources?: string[];
      type?: string;
    };
  }
  
  export type ApiError = {
    message: string;
    code?: number;
  };