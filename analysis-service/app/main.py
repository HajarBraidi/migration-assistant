from fastapi import FastAPI, File, HTTPException, UploadFile

from app.analyse import analyser
from app.archive import ArchiveInvalide, lire_archive
from app.config import settings
from app.schemas import AnalyseResultat

app = FastAPI(
    title="analysis-service",
    description="Analyse le code d'un projet (PHP, Java, Node.js) : technologies, "
    "incompatibilités et préparation au cloud.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "analysis-service"}


@app.post("/analyses", response_model=AnalyseResultat)
async def analyser_archive(archive: UploadFile = File(...)) -> AnalyseResultat:
    """Analyse une archive .zip du projet. Rien n'est conservé après l'analyse."""
    if not (archive.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Déposez une archive .zip du projet.")

    limite = settings.taille_max_archive_mo * 1024 * 1024
    contenu = await archive.read(limite + 1)
    if len(contenu) > limite:
        raise HTTPException(
            status_code=413, detail=f"L'archive dépasse {settings.taille_max_archive_mo} Mo."
        )
    try:
        projet = lire_archive(contenu)
    except ArchiveInvalide as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return analyser(projet)
