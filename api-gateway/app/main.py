import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="api-gateway",
    description="Point d'entrée unique de l'API : vérifie l'utilisateur et transmet les requêtes.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remplaçable dans les tests par un faux réseau
_transport: httpx.AsyncBaseTransport | None = None


async def relayer(request: Request, url: str, entetes: dict | None = None) -> Response:
    """Transmet la requête au service cible et renvoie sa réponse telle quelle."""
    try:
        async with httpx.AsyncClient(
            transport=_transport, timeout=settings.request_timeout_seconds
        ) as client:
            reponse = await client.request(
                request.method,
                url,
                content=await request.body(),
                headers={
                    "Content-Type": request.headers.get("content-type", "application/json"),
                    **(entetes or {}),
                },
                params=request.query_params,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Service indisponible : {exc}") from exc

    return Response(
        content=reponse.content,
        status_code=reponse.status_code,
        media_type=reponse.headers.get("content-type"),
    )


def utilisateur_connecte(authorization: str = Header(default="")) -> str:
    """Vérifie le jeton JWT et renvoie l'identifiant de l'utilisateur."""
    jeton = authorization.removeprefix("Bearer ").strip()
    if not jeton:
        raise HTTPException(status_code=401, detail="Connexion requise.")
    try:
        contenu = jwt.decode(jeton, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée.") from exc
    return contenu["sub"]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api-gateway"}


# ---------- Authentification (routes publiques) ----------


@app.post("/api/auth/register")
async def inscription(request: Request) -> Response:
    return await relayer(request, f"{settings.auth_service_url}/register")


@app.post("/api/auth/login")
async def connexion(request: Request) -> Response:
    return await relayer(request, f"{settings.auth_service_url}/login")


@app.get("/api/auth/me")
async def moi(request: Request) -> Response:
    entetes = {"Authorization": request.headers.get("authorization", "")}
    return await relayer(request, f"{settings.auth_service_url}/me", entetes)


# ---------- Projets (routes protégées) ----------


@app.api_route("/api/projects", methods=["GET", "POST"])
async def projets(request: Request, user_id: str = Depends(utilisateur_connecte)) -> Response:
    """Historique (GET) ou création d'un projet (POST) de l'utilisateur connecté."""
    return await relayer(
        request, f"{settings.project_service_url}/projects", {"X-User-Id": user_id}
    )


@app.get("/api/projects/{project_id}")
async def projet(
    project_id: int, request: Request, user_id: str = Depends(utilisateur_connecte)
) -> Response:
    """Un projet précis de l'utilisateur connecté."""
    return await relayer(
        request, f"{settings.project_service_url}/projects/{project_id}", {"X-User-Id": user_id}
    )
