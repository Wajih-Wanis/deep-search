from typing import List, TypedDict, Annotated
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
