import io
import zipfile

from fastapi import FastAPI, Response

from app.kit import generer
from app.schemas import DemandeKit, Kit

app = FastAPI(
    title="deploy-service",
    description="Génère le kit de déploiement : Dockerfile, Terraform, pipeline CI/CD, "
    "scripts de migration de la base et guide pas à pas.",
    version="0.1.0",
)

# Scripts à rendre exécutables dans l'archive
EXECUTABLES = (".sh",)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "deploy-service"}


@app.post("/kits", response_model=Kit)
def apercu_kit(demande: DemandeKit) -> Kit:
    """Le kit, fichier par fichier (pour l'aperçu dans l'interface)."""
    return generer(demande)


@app.post("/kits/archive")
def archive_kit(demande: DemandeKit) -> Response:
    """Le kit complet dans une archive .zip, prête à extraire à la racine du projet."""
    kit = generer(demande)
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w", zipfile.ZIP_DEFLATED) as archive:
        for fichier in kit.fichiers:
            info = zipfile.ZipInfo(f"{kit.projet}-kit/{fichier.chemin}")
            info.compress_type = zipfile.ZIP_DEFLATED
            droits = 0o755 if fichier.chemin.endswith(EXECUTABLES) else 0o644
            info.external_attr = (0o100000 | droits) << 16
            archive.writestr(info, fichier.contenu)
    return Response(
        content=tampon.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{kit.projet}-kit-deploiement.zip"'},
    )
