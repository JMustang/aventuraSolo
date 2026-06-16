from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class StoryOptionsSchema(BaseModel):
    text: str
    node_id: Optional[int] = None


class StoryNodeBase(BaseModel):
    content: str
    is_ending: bool = False
    is_winning_ending: bool = False


class CompleteStoryNodeResponse(StoryNodeBase):
    id: int
    options: List[StoryOptionsSchema] = []

    class Config:
        from_attributes = True


class StoryBase(BaseModel):
    title: str
    session_id: Optional[str] = None

    class Config:
        from_attributes = True


class StoryCatalogItem(BaseModel):
    slug: str
    title: str
    theme: str


class StoryCatalogResponse(BaseModel):
    themes: List[str]
    stories: List[StoryCatalogItem]


class CreateStoryRequest(BaseModel):
    theme: str
    story_slug: Optional[str] = Field(
        default=None,
        description="Slug da história. Se omitido, uma história aleatória do tema é escolhida.",
    )


class CompleteStoryResponse(StoryBase):
    id: int
    created_at: datetime
    root_node: CompleteStoryNodeResponse
    all_nodes: Dict[int, CompleteStoryNodeResponse]

    class Config:
        from_attributes = True
