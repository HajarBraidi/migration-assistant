from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    """Transforme le mot de passe en empreinte irréversible (bcrypt + sel aléatoire)."""
    return bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt()).decode()


def verifier_mot_de_passe(mot_de_passe: str, empreinte: str) -> bool:
    """Vérifie un mot de passe sans jamais le stocker en clair."""
    return bcrypt.checkpw(mot_de_passe.encode(), empreinte.encode())


def creer_jeton(user_id: int, nom: str) -> str:
    """Crée un jeton JWT signé, valable pendant une durée limitée."""
    maintenant = datetime.now(timezone.utc)
    contenu = {
        "sub": str(user_id),
        "nom": nom,
        "iat": maintenant,
        "exp": maintenant + timedelta(minutes=settings.jwt_duree_minutes),
    }
    return jwt.encode(contenu, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def lire_jeton(jeton: str) -> int | None:
    """Renvoie l'identifiant de l'utilisateur si le jeton est valide, sinon None."""
    try:
        contenu = jwt.decode(jeton, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
    return int(contenu["sub"])
