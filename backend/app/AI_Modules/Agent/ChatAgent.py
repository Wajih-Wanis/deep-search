from typing import List, Dict
import logging

class ChatAgent:
    def __init__(self, model):
        self.model = model
        
    def _generate_message(self, user_message: str, history: List[Dict[str, str]]) -> str:
        """Maintains original interface while fixing context formatting"""
        try:
            context = self._format_history(history, user_message)
            return self.model._run(context)
        except Exception as e:
            logging.error(f"Chat error: {str(e)}")
            return "Sorry, I encountered an error processing your message."

    def _format_history(self, history: List[Dict], current_message: str) -> str:
        """Formats conversation history with clear speaker identification"""
        context = []
        
        for msg in history[-3:]:  
            role = "User" if msg["role"] == "user" else "Assistant"
            context.append(f"{role}: {msg['content']}")
        
        context.append(f"User: {current_message}")
        context.append("Assistant:")
        
        return "\n".join(context)