import React from "react";

export const ChatTextInput = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement> 
>(({ ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className="p-4 w-full focus:outline-none bg-transparent resize-none "
      placeholder="Type your message here..."
      {...props}
    />
  );
});
ChatTextInput.displayName = "ChatTextInput";