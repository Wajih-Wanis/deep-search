from typing import List
from pydantic import BaseModel


class Website(BaseModel): 
    url : str 
    title : str 
    content : str | None 