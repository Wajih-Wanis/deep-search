from abc import ABC,abstractmethod
from langchain_ollama import OllamaLLM


class Model:
    
    @abstractmethod
    def __init__(self):
        pass 
    
    
    @abstractmethod
    def _run(self):
        pass


class OllamaModel(Model):
    
    def __init__(self,model="deepseek-r1:8b"):
        self.model = OllamaLLM(model=model) 
        
    
    def _run(self,input:str) -> str:
        return self.model.invoke(input)        