import { useEffect, useMemo, useState } from "react";
import { AlertCircle, AlertTriangle, Download, FileCode2, Loader2 } from "lucide-react";
import { api } from "../api.js";

const FOURNISSEURS = ["AWS", "Azure", "GCP", "OVHcloud"];
const BASES = ["PostgreSQL", "MySQL"];
const LANGAGES = ["PHP", "Java", "JavaScript"];
const CATEGORIES = ["Guide", "Application", "Infrastructure", "Déploiement", "Base de données"];

// Base cible proposée : on garde le moteur actuel s'il est libre, sinon PostgreSQL
const baseParDefaut = (source) => (source === "MySQL" ? "MySQL" : "PostgreSQL");

export default function DeploymentKit({ description }) {
  const [fournisseur, setFournisseur] = useState(
    FOURNISSEURS.includes(description.hebergement_cible) ? description.hebergement_cible : "AWS"
  );
  const [base, setBase] = useState(baseParDefaut(description.type_base_donnees));
  const [kit, setKit] = useState(null);
  const [erreur, setErreur] = useState("");
  const [ouvert, setOuvert] = useState("GUIDE-DEPLOIEMENT.md");
  const [telechargement, setTelechargement] = useState(false);

  const compatible = LANGAGES.includes(description.langage);
  const demande = useMemo(
    () => ({
      nom: description.nom,
      langage: description.langage,
      framework_backend: description.framework_backend || null,
      type_base_donnees: description.type_base_donnees,
      base_cible: base,
      fournisseur,
      nombre_utilisateurs: description.nombre_utilisateurs,
      volume_donnees: description.volume_donnees,
      haute_disponibilite: description.interruption_acceptable === "Aucune",
    }),
    [description, base, fournisseur]
  );

  useEffect(() => {
    if (!compatible) return;
    let actif = true;
    setKit(null);
    setErreur("");
    api
      .apercuKit(demande)
      .then((resultat) => actif && setKit(resultat))
      .catch((e) => actif && setErreur(e.message));
    return () => {
      actif = false;
    };
  }, [demande, compatible]);

  if (!compatible) {
    return (
      <div className="alert alert-warning">
        <AlertTriangle size={18} />
        <span>
          Le kit de déploiement est disponible pour les applications PHP, Java et JavaScript (Node.js).
          Langage de ce projet : {description.langage}.
        </span>
      </div>
    );
  }

  const telecharger = async () => {
    setTelechargement(true);
    setErreur("");
    try {
      await api.telechargerKit(demande);
    } catch (e) {
      setErreur(e.message);
    } finally {
      setTelechargement(false);
    }
  };

  // Si le fichier ouvert n'existe pas pour ce fournisseur (ex. main.tf chez OVHcloud), on revient au guide
  const fichierOuvert =
    kit?.fichiers.find((f) => f.chemin === ouvert) ||
    kit?.fichiers.find((f) => f.chemin === "GUIDE-DEPLOIEMENT.md");

  return (
    <div className="kit">
      <div className="kit-tete">
        <p className="couts-hypotheses">
          Fichiers prêts à l'emploi, générés à partir de <strong>modèles vérifiés</strong> (sans IA) :
          conteneur, infrastructure Terraform, pipeline GitHub Actions, scripts de migration de la base et guide.
        </p>
        <div className="kit-choix">
          <div>
            <span className="kit-libelle">Fournisseur</span>
            <div className="segment">
              {FOURNISSEURS.map((f) => (
                <button key={f} className={fournisseur === f ? "actif" : ""} onClick={() => setFournisseur(f)}>
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="kit-libelle">Nouvelle base</span>
            <div className="segment">
              {BASES.map((b) => (
                <button key={b} className={base === b ? "actif" : ""} onClick={() => setBase(b)}>
                  {b}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {erreur && (
        <div className="alert alert-error">
          <AlertCircle size={18} />
          <span>{erreur}</span>
        </div>
      )}
      {!kit && !erreur && (
        <div className="cout-chargement">
          <Loader2 size={18} className="spin" />
          Préparation du kit…
        </div>
      )}

      {kit && (
        <>
          {kit.avertissements.length > 0 && (
            <div className="alert alert-warning">
              <AlertTriangle size={18} />
              {kit.avertissements.length === 1 ? (
                <span>{kit.avertissements[0]}</span>
              ) : (
                <ul>
                  {kit.avertissements.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="kit-corps">
            <nav className="kit-fichiers" aria-label="Fichiers du kit">
              {CATEGORIES.map((categorie) => {
                const liste = kit.fichiers.filter((f) => f.categorie === categorie);
                if (!liste.length) return null;
                return (
                  <div key={categorie} className="kit-groupe">
                    <span className="kit-libelle">{categorie}</span>
                    {liste.map((f) => (
                      <button
                        key={f.chemin}
                        className={`kit-fichier ${fichierOuvert?.chemin === f.chemin ? "actif" : ""}`}
                        onClick={() => setOuvert(f.chemin)}
                        title={f.description}
                      >
                        <FileCode2 size={14} />
                        <span>{f.chemin}</span>
                      </button>
                    ))}
                  </div>
                );
              })}
            </nav>

            {fichierOuvert && (
              <div className="kit-apercu">
                <div className="kit-apercu-tete">
                  <strong>{fichierOuvert.chemin}</strong>
                  <span className="muted">{fichierOuvert.description}</span>
                </div>
                <pre>
                  <code>{fichierOuvert.contenu}</code>
                </pre>
              </div>
            )}
          </div>

          <div className="kit-actions">
            <span className="couts-avertissement">
              {kit.fichiers.length} fichiers. Extrayez l'archive à la racine de votre projet, puis suivez
              GUIDE-DEPLOIEMENT.md. Aucun mot de passe n'est inclus.
            </span>
            <button className="btn btn-primary" onClick={telecharger} disabled={telechargement}>
              {telechargement ? <Loader2 size={16} className="spin" /> : <Download size={16} />}
              Télécharger le kit (.zip)
            </button>
          </div>
        </>
      )}
    </div>
  );
}
