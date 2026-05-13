from sqlalchemy.orm import Session
from .config import settings

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .prompts import STORY_PROMPT
from models.story import Story
