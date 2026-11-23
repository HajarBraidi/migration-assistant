from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Limites de l'analyse : elles protègent le service contre les archives trop lourdes."""

    taille_max_archive_mo: int = 20
    taille_max_decompressee_mo: int = 100
    nombre_max_fichiers: int = 5000
    taille_max_fichier_ko: int = 1024  # au-delà, un fichier n'est pas lu


settings = Settings()
