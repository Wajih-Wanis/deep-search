from abc import ABC,abstractmethod
from langchain_ollama import OllamaLLM
from ollama import ListResponse, list

class Model:
    
    @classmethod
    @abstractmethod
    def _get_model(self):
        pass
    
    @abstractmethod
    def __init__(self):
        pass 
    
    
    @abstractmethod
    def _run(self):
        pass


class OllamaModel(Model):  
    
    @classmethod
    def _get_model(self):
        response: ListResponse = list()
        result = dict()
        for model in response.models:
            result.update({model.model:model.size.real/1024/1024})
        
    def __init__(self,model="llama3.2:1b",temperature=0):
        self.model = OllamaLLM(model=model,temperature=temperature) 
        
    
    def _run(self,input:str) -> str:
        return self.model.invoke(input)        
    