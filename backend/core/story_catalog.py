import json
import random
from pathlib import Path
from typing import List, Optional

from .models import StoryLLMResponse, StoryTemplateMeta

STORIES_DIR = Path(__file__).parent.parent / "data" / "stories"


class StoryCatalog:
    @classmethod
    def list_themes(cls) -> List[str]:
        if not STORIES_DIR.exists():
            return []

        return sorted(
            folder.name
            for folder in STORIES_DIR.iterdir()
            if folder.is_dir() and not folder.name.startswith(".")
        )

    @classmethod
    def list_stories(cls, theme: Optional[str] = None) -> List[StoryTemplateMeta]:
        stories: List[StoryTemplateMeta] = []

        if not STORIES_DIR.exists():
            return stories

        theme_dirs = (
            [STORIES_DIR / theme]
            if theme
            else [folder for folder in STORIES_DIR.iterdir() if folder.is_dir()]
        )

        for theme_dir in theme_dirs:
            if not theme_dir.exists():
                continue

            for story_file in sorted(theme_dir.glob("*.json")):
                template = cls._load_file(story_file)
                stories.append(
                    StoryTemplateMeta(
                        slug=template.slug,
                        title=template.title,
                        theme=template.theme,
                    )
                )

        return stories

    @classmethod
    def get_story(
        cls, theme: str, story_slug: Optional[str] = None
    ) -> StoryLLMResponse:
        theme_dir = STORIES_DIR / theme

        if not theme_dir.exists():
            available = ", ".join(cls.list_themes()) or "nenhum"
            raise ValueError(
                f"Tema '{theme}' não encontrado. Temas disponíveis: {available}"
            )

        story_files = sorted(theme_dir.glob("*.json"))
        if not story_files:
            raise ValueError(f"Nenhuma história cadastrada para o tema '{theme}'.")

        if story_slug:
            story_file = theme_dir / f"{story_slug}.json"
            if not story_file.exists():
                available = ", ".join(file.stem for file in story_files)
                raise ValueError(
                    f"História '{story_slug}' não encontrada em '{theme}'. "
                    f"Disponíveis: {available}"
                )
            return cls._load_file(story_file)

        return cls._load_file(random.choice(story_files))

    @classmethod
    def _load_file(cls, story_file: Path) -> StoryLLMResponse:
        with open(story_file, encoding="utf-8") as file:
            data = json.load(file)

        if "slug" not in data:
            data["slug"] = story_file.stem

        if "theme" not in data:
            data["theme"] = story_file.parent.name

        return StoryLLMResponse.model_validate(data)
