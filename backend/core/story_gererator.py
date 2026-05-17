from sqlalchemy.orm import Session

import os
import requests

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from .prompts import STORY_PROMPT
from models.story import Story, StoryNode
from .models import StoryLLMResponse, StoryNodeLLM
from dotenv import load_dotenv

load_dotenv()


class StoryGenerator:

    @classmethod
    def _call_deepseek(cls, prompt_text: str) -> str:
        """Chama a API do Deepseek e retorna o texto da resposta.

        Observação: ajuste `endpoint` e a extração do texto conforme a resposta real
        da API do Deepseek (este é um template genérico).
        """
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY não definido. Exporte a variável de ambiente."
            )

        endpoint = os.getenv(
            "DEEPSEEK_API_ENDPOINT",
            "https://api.deepseek.ai/v1/chat/completions",
        )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-3.5",
            "messages": [{"role": "user", "content": prompt_text}],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        resp = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extrair conteúdo. Alguns providers usam data['choices'][0]['message']['content']
        # ou data['choices'][0]['text']. Ajuste conforme a resposta real do Deepseek.
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            try:
                return data["choices"][0]["text"]
            except Exception:
                # fallback: stringify
                return str(data)

    @classmethod
    def generate_story(
        cls, db: Session, session_id: str, theme: str = "fantasy"
    ) -> Story:
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)

        # Monta o prompt final combinando instruções de sistema, prompt do user
        # e as instruções de formatação do parser.
        prompt_text = (
            f"{STORY_PROMPT}\n\nCria uma historia com esse tema: {theme}\n\n"
            f"{story_parser.get_format_instructions()}"
        )

        response_text = cls._call_deepseek(prompt_text)

        story_structure = story_parser.parse(response_text)

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        return story_db

    @classmethod
    def _process_story_node(
        cls, db: Session, story_id: int, node_data: StoryNodeLLM, is_root: bool = False
    ) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=(
                node_data.content
                if hasattr(node_data, "content")
                else node_data["content"]
            ),
            is_root=is_root,
            is_ending=(
                node_data.isEnding
                if hasattr(node_data, "isEnding")
                else node_data["isEnding"]
            ),
            is_winning_ending=(
                node_data.isWinningEnding
                if hasattr(node_data, "isWinningEnding")
                else node_data["isWinningEnding"]
            ),
            options=[],
        )
        db.add(node)
        db.flush()

        if not node.is_ending and (hasattr(node_data, "options") and node_data.options):
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(
                    db, story_id, next_node, is_root=False
                )

                options_list.append(
                    {"text": option_data.text, "node_id": child_node.id}
                )
            node.options = options_list

        db.flush()
        return node
