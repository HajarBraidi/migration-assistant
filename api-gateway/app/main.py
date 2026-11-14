import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="api-gateway",
    description="Point d'entrée unique de l'API : transmet les requêtes aux services.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remplaçable dans les tests par un faux réseau
_transport: httpx.AsyncBaseTransport | None = None


async def relayer(request: Request, url: str) -> Response:
    """Transmet la requête au service cible et renvoie sa réponse telle quelle."""
    try:
        async with httpx.AsyncClient(
            transport=_transport, timeout=settings.request_timeout_seconds
        ) as client:
            reponse = await client.request(
                request.method,
                url,
                content=await request.body(),
                headers={"Content-Type": request.headers.get("content-type", "application/json")},
                params=request.query_params,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail=f"Service indisponible : {exc}") from exc

    return Response(
        content=reponse.content,
        status_code=reponse.status_code,
        media_type=reponse.headers.get("content-type"),
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "api-gateway"}


@app.api_route("/api/projects", methods=["GET", "POST"])
async def projets(request: Request) -> Response:
    """Historique (GET) ou création d'un projet (POST)."""
    return await relayer(request, f"{settings.project_service_url}/projects")


@app.get("/api/projects/{project_id}")
async def projet(project_id: int, request: Request) -> Response:
    """Un projet précis."""
    return await relayer(request, f"{settings.project_service_url}/projects/{project_id}")