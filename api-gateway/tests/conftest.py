import os

os.environ.setdefault("JWT_SECRET", "secret-de-test")

from datetime import datetime, timedelta, timezone  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.main as gateway  # noqa: E402
from app.config import settings  # noqa: E402
from app.main import app  # noqa: E402


def jeton(user_id: int = 7, secret: str | None = None, minutes: int = 30) -> dict:
    """En-tête Authorization avec un jeton JWT signé par le secret du gateway."""
    contenu = {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)}
    secret = secret or settings.jwt_secret
    return {"Authorization": f"Bearer {jwt.encode(contenu, secret, algorithm='HS256')}"}


@pytest.fixture
def client():
    yield TestClient(app)
    gateway._transport = None
