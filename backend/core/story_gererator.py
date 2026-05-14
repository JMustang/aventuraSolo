from sqlalchemy.orm import Session
from .config import settings

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .prompts import STORY_PROMPT
from models.story import Story
from .models import StoryLLMResponse, StoryNodeLLM


class StoryGenerator:

    @classmethod
    def _get_llm(cls):
        return ChatOpenAI(model="deepseek-3.5", temperature=0.7, max_token=2048)

    @classmethod
    def generate_story(
        cls, db: Session, session_id: str, theme: str = "fantasy"
    ) -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", STORY_PROMPT),
                ("human", f"Cria uma historia com esse tema: {theme}"),
            ]
        ).partial(format_instructions=story_parser.get_format_instructions())

        raw_response = llm.invoke(prompt.invoke({}))

        response_text = raw_response
        if hasattr(raw_response, "content"):
            response_text = raw_response.content

        story_structure = story_parser.parse(response_text)
