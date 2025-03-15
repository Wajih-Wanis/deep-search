"use client";

import { useEffect } from "react";
import { useChatUI } from "@/hooks/use-chat-ui";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircleIcon } from "lucide-react";

export function ErrorBoundary({ children, error }: { 
  children?: React.ReactNode;
  error?: string 
}) {
  const { error: contextError, setError } = useChatUI();

  useEffect(() => {
    if (error) setError(error);
  }, [error, setError]);

  const message = error || contextError;
  
  return (
    <>
      {message && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircleIcon className="h-4 w-4" />
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      )}
      {children}
    </>
  );
}