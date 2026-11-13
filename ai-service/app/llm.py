import logging
import time

from google import genai
from google.genai import errors, types

from app.config import settings

logger = logging.getLogger(__name__)

# Erreurs temporaires : il est utile de réessayer
ERREURS_TEMPORAIRES = {429, 500, 503, 504}


class LLMError(Exception):
    """Erreur lors de l'appel au LLM."""


_client = genai.Client(
    api_key=settings.gemini_api_key,
    http_options=types.HttpOptions(timeout=settings.llm_timeout_seconds * 1000),
)


def _modeles() -> list[str]:
    """Modèle principal, puis modèle de secours s'il est configuré."""
    modeles = [settings.gemini_model]
    if settings.gemini_fallback_model:
        modeles.append(settings.gemini_fallback_model)
    return modeles


def _call(prompt: str, config: types.GenerateContentConfig | None = None) -> str:
    """Appelle le LLM avec nouvelles tentatives et modèle de secours."""
    derniere_erreur: Exception | None = None

    for modele in _modeles():
        for tentative in range(settings.llm_max_retries):
            try:
                response = _client.models.generate_content(
                    model=modele,
                    contents=prompt,
                    config=config,
                )
            except errors.APIError as exc:
                derniere_erreur = exc
                if exc.code not in ERREURS_TEMPORAIRES:
                    raise LLMError(f"Erreur lors de l'appel au LLM : {exc}") from exc
                attente = 2**tentative  # 1 s, puis 2 s, puis 4 s
                logger.warning(
                    "Modèle %s indisponible (code %s), nouvelle tentative dans %s s",
                    modele, exc.code, attente,
                )
                time.sleep(attente)
                continue
            except Exception as exc:
                raise LLMError(f"Erreur lors de l'appel au LLM : {exc}") from exc

            if not response.text:
                raise LLMError("Le LLM a renvoyé une réponse vide.")
            return response.text

        logger.warning("Passage au modèle suivant après l'échec de %s", modele)

    raise LLMError(f"LLM indisponible après plusieurs tentatives : {derniere_erreur}")


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