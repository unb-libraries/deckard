from pydantic import BaseModel
from typing import List, Optional

class Link(BaseModel):
    label: str
    url: str

class Question(BaseModel):
    queries: List[str]
    response: str
    links: Optional[List[Link]]

class QAFile(BaseModel):
    questions: List[Question]
