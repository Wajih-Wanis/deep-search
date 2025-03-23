from typing import List, TypedDict, Annotated, Dict, Any
import operator
from pydantic import BaseModel


class Website(BaseModel): 
    url : str 
    title : str 
    content : str | None 

class SearchQueries(BaseModel):
    queries: list[str]

class RelevanceScore(BaseModel):
    score: float
    reason: str

class FinalResponse(BaseModel):
    summary: str
    sources: list[str]

class Document(TypedDict):
    page_content: str
    metadata: Dict[str, Any]
    
class QueryResult(TypedDict):
    answer: str
    sources: List[str]