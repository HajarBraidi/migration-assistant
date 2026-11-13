from google import genai
from google.genai import types

from app.config import settings


class LLMError(Exception):
    """Erreur lors de l'appel au LLM."""


_client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(timeout=settings.llm_timeout_seconds * 1000),
)


def _call(prompt: str, config: types.GenerateContentConfig | None = None) -> str:
    """Appelle le LLM et renvoie le texte de sa réponse."""
    try:
        response = _client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=config,
        )
    except Exception as exc:
        raise LLMError(f"Erreur lors de l'appel au LLM : {exc}") from exc

    if not response.text:
        raise LLMError("Le LLM a renvoyé une réponse vide.")
    return response.text


def generate_text(prompt: str) -> str:
    """Réponse en texte libre."""
    return _call(prompt)


def generate_json(prompt: str) -> str:
    """Réponse obligatoirement au format JSON."""
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.3,
    )
    return _call(prompt, config)