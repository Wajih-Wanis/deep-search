import logging

class ChatAgent:
    
    def __init__(self,model):
        self.model = model
        
        
    def _generate_message(self,user_message,history):
        try:
            context = ""
            for msg in history:
                context+=f"{msg['role']} {msg['content']}" 
            context+=" user"+user_message
            response = self.model._run(context)
            return response
        except Exception as e:
            logging.info(f"Could generate chat {e} occured")
            print(e)
        return ''