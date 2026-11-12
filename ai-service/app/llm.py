from google import genai
from google.genai import types

from app.config import settings


class LLMError(Exception):
    """Erreur lors de l'appel au LLM."""


_client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(timeout=settings.llm_timeout_seconds * 1000),
)


def generate_text(prompt: str) -> str:
    """Envoie un prompt au LLM et renvoie sa réponse en texte."""
    try:
        response = _client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
    except Exception as exc:
        raise LLMError(f"Erreur lors de l'appel au LLM : {exc}") from exc

    if not response.text:
        raise LLMError("Le LLM a renvoyé une réponse vide.")
    return response.text