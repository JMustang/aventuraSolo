import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from pydantic import ValidationError

from core.models import StoryLLMResponse, StoryNodeLLM
from core.story_catalog import STORIES_DIR

PLACEHOLDER_PREFIX = "SUBSTITUA"


@dataclass
class StoryValidationResult:
    file: Path
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    has_winning_ending: bool = False
    has_any_ending: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_story_file(story_file: Path) -> StoryValidationResult:
    result = StoryValidationResult(file=story_file.resolve())

    if not story_file.exists():
        result.errors.append("Arquivo não encontrado.")
        return result

    if story_file.suffix.lower() != ".json":
        result.errors.append("O arquivo deve ter extensão .json.")
        return result

    try:
        with open(story_file, encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        result.errors.append(f"JSON inválido: {exc}")
        return result

    if not isinstance(data, dict):
        result.errors.append("A história deve ser um objeto JSON.")
        return result

    data = _apply_defaults(story_file, data)

    try:
        story = StoryLLMResponse.model_validate(data)
    except ValidationError as exc:
        for error in exc.errors():
            location = ".".join(str(part) for part in error["loc"])
            result.errors.append(f"{location}: {error['msg']}")
        return result

    _validate_metadata(story_file, story, result)
    _validate_node(story.rootNode, "rootNode", result)

    if not result.has_any_ending:
        result.errors.append(
            "A história precisa ter pelo menos um final (isEnding=true)."
        )

    if not result.has_winning_ending:
        result.errors.append(
            "A história precisa ter pelo menos um final vencedor "
            "(isEnding=true e isWinningEnding=true)."
        )

    return result


def validate_all_stories() -> List[StoryValidationResult]:
    results: List[StoryValidationResult] = []
    slugs_by_theme: dict[str, set[str]] = {}

    if not STORIES_DIR.exists():
        return results

    for theme_dir in sorted(STORIES_DIR.iterdir()):
        if not theme_dir.is_dir() or theme_dir.name.startswith("."):
            continue

        for story_file in sorted(theme_dir.glob("*.json")):
            result = validate_story_file(story_file)
            results.append(result)

            if result.ok:
                theme = story_file.parent.name
                slug = story_file.stem
                theme_slugs = slugs_by_theme.setdefault(theme, set())
                if slug in theme_slugs:
                    result.errors.append(
                        f"Slug duplicado no tema '{theme}': '{slug}'."
                    )
                theme_slugs.add(slug)

    return results


def _apply_defaults(story_file: Path, data: dict) -> dict:
    prepared = dict(data)

    if "slug" not in prepared:
        prepared["slug"] = story_file.stem

    if "theme" not in prepared:
        prepared["theme"] = story_file.parent.name

    return prepared


def _validate_metadata(
    story_file: Path, story: StoryLLMResponse, result: StoryValidationResult
) -> None:
    for field_name, value in (
        ("slug", story.slug),
        ("title", story.title),
        ("theme", story.theme),
    ):
        if not value or not str(value).strip():
            result.errors.append(f"O campo '{field_name}' não pode ficar vazio.")
        elif str(value).startswith(PLACEHOLDER_PREFIX):
            result.errors.append(
                f"O campo '{field_name}' ainda contém placeholder ({PLACEHOLDER_PREFIX})."
            )

    if _is_theme_story_file(story_file):
        if story_file.stem != story.slug:
            result.warnings.append(
                f"O slug '{story.slug}' difere do nome do arquivo '{story_file.stem}'. "
                "Recomendado manter iguais."
            )

        if story_file.parent.name != story.theme:
            result.warnings.append(
                f"O theme '{story.theme}' difere da pasta '{story_file.parent.name}'. "
                "Recomendado manter iguais."
            )


def _validate_node(
    node: StoryNodeLLM, path: str, result: StoryValidationResult
) -> None:
    if not node.content or not node.content.strip():
        result.errors.append(f"{path}.content não pode ficar vazio.")
    elif node.content.startswith(PLACEHOLDER_PREFIX):
        result.errors.append(
            f"{path}.content ainda contém placeholder ({PLACEHOLDER_PREFIX})."
        )

    if node.isEnding:
        result.has_any_ending = True

        if node.isWinningEnding:
            result.has_winning_ending = True

        if node.options:
            result.errors.append(
                f"{path}: nós finais não devem ter opções (use options: [])."
            )
        return

    if node.isWinningEnding:
        result.errors.append(
            f"{path}: isWinningEnding só pode ser true em nós finais (isEnding=true)."
        )

    options = node.options or []
    if not options:
        result.errors.append(
            f"{path}: nós que não são finais precisam ter pelo menos uma opção."
        )
        return

    for index, option in enumerate(options):
        option_path = f"{path}.options[{index}]"

        if not option.text or not option.text.strip():
            result.errors.append(f"{option_path}.text não pode ficar vazio.")
        elif option.text.startswith(PLACEHOLDER_PREFIX):
            result.errors.append(
                f"{option_path}.text ainda contém placeholder ({PLACEHOLDER_PREFIX})."
            )

        if not option.nextNode:
            result.errors.append(f"{option_path}.nextNode é obrigatório.")
            continue

        next_node = StoryNodeLLM.model_validate(option.nextNode)
        _validate_node(next_node, f"{option_path}.nextNode", result)


def _is_theme_story_file(story_file: Path) -> bool:
    try:
        return story_file.parent.resolve() != STORIES_DIR.resolve()
    except ValueError:
        return story_file.parent != STORIES_DIR
