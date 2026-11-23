import { useRef, useState } from "react";
import {
  AlertCircle, ArrowRight, Boxes, ChevronDown, FileCode2, Loader2, Lock, RotateCcw,
  ShieldAlert, Sparkles, UploadCloud,
} from "lucide-react";
import { api } from "../api.js";

const TAILLE_MAX_MO = 20;
const GRAVITES = { Bloquant: "high", Important: "medium", Conseil: "neutral" };
const FILTRES = ["Tous", "Compatibilité", "Sécurité", "Cloud"];

function niveauScore(score) {
  if (score >= 80) return { classe: "bon", libelle: "Prêt pour le cloud" };
  if (score >= 50) return { classe: "moyen", libelle: "Préparation nécessaire" };
  return { classe: "faible", libelle: "Travail important avant migration" };
}

// Jauge circulaire du score de préparation
function JaugeScore({ score }) {
  const { classe, libelle } = niveauScore(score);
  const rayon = 52;
  const circonference = 2 * Math.PI * rayon;
  return (
    <div className={`score score-${classe}`}>
      <svg viewBox="0 0 120 120" width="132" height="132" aria-hidden="true">
        <circle cx="60" cy="60" r={rayon} className="score-fond" />
        <circle
          cx="60" cy="60" r={rayon} className="score-valeur"
          strokeDasharray={circonference}
          strokeDashoffset={circonference * (1 - score / 100)}
        />
      </svg>
      <div className="score-texte">
        <span className="score-nombre">{score}</span>
        <span className="score-sur">/ 100</span>
      </div>
      <div className="score-libelle">{libelle}</div>
    </div>
  );
}

function ProblemeCarte({ probleme }) {
  const [ouvert, setOuvert] = useState(false);
  const nombre = probleme.total;
  return (
    <article className={`probleme probleme-${GRAVITES[probleme.gravite]}`}>
      <header className="probleme-tete">
        <span className={`badge badge-${GRAVITES[probleme.gravite]}`}>{probleme.gravite}</span>
        <h3>{probleme.titre}</h3>
        <span className="badge badge-outline">{probleme.categorie}</span>
      </header>
      <p className="probleme-explication">{probleme.explication}</p>
      <p className="probleme-correction"><strong>Correction :</strong> {probleme.correction}</p>
      {probleme.occurrences.length > 0 && (
        <>
          <button className="lien-occurrences" onClick={() => setOuvert(!ouvert)} aria-expanded={ouvert}>
            <ChevronDown size={16} className={ouvert ? "pivote" : ""} />
            {nombre} occurrence{nombre > 1 ? "s" : ""} dans le code
          </button>
          {ouvert && (
            <ul className="occurrences">
              {probleme.occurrences.map((o) => (
                <li key={`${o.fichier}:${o.ligne}`}>
                  <span className="occurrence-lieu">{o.fichier}<span>:{o.ligne}</span></span>
                  <code>{o.extrait}</code>
                </li>
              ))}
              {nombre > probleme.occurrences.length && (
                <li className="muted">… et {nombre - probleme.occurrences.length} autre(s)</li>
              )}
            </ul>
          )}
        </>
      )}
    </article>
  );
}

function Resultats({ resultat, nomFichier, onCreerPlan, onRecommencer }) {
  const [filtre, setFiltre] = useState("Tous");
  const { pile, statistiques, resume } = resultat;
  const problemes = resultat.problemes.filter((p) => filtre === "Tous" || p.categorie === filtre);
  const lignesPile = [
    ["Langage", [pile.langage, pile.version_langage].filter(Boolean).join(" ")],
    ["Framework", pile.framework],
    ["Interface", pile.interface],
    ["Base de données", pile.base_de_donnees],
    ["Architecture", pile.architecture],
    ["Intégrations", pile.integrations.join(", ")],
  ];

  return (
    <>
      <section className="card analyse-synthese">
        <JaugeScore score={resultat.score_preparation} />
        <div className="analyse-pile">
          <p className="eyebrow">Projet analysé : {nomFichier}</p>
          <dl>
            {lignesPile.map(([libelle, valeur]) => (
              <div key={libelle}>
                <dt>{libelle}</dt>
                <dd>{valeur || <span className="muted">Non détecté</span>}</dd>
              </div>
            ))}
          </dl>
          <p className="muted analyse-stats">
            {statistiques.fichiers} fichiers · {statistiques.lignes_de_code.toLocaleString("fr-FR")} lignes de code analysées
            · {resultat.dependances.length} dépendances
          </p>
        </div>
      </section>

      <div className="kpis kpis-3">
        <div className="kpi kpi-high"><ShieldAlert size={18} /><div><div className="kpi-label">Bloquants</div><div className="kpi-value">{resume.bloquants}</div></div></div>
        <div className="kpi kpi-medium"><AlertCircle size={18} /><div><div className="kpi-label">Importants</div><div className="kpi-value">{resume.importants}</div></div></div>
        <div className="kpi"><FileCode2 size={18} /><div><div className="kpi-label">Conseils</div><div className="kpi-value">{resume.conseils}</div></div></div>
      </div>

      <section className="card cta">
        <div>
          <h2>Générer le plan de migration</h2>
          <p className="subtitle">
            <strong>{resultat.champs_detectes.length + resultat.champs_a_verifier.length}</strong> champs du
            formulaire seront pré-remplis ({resultat.champs_a_verifier.length} à vérifier). Il vous
            restera surtout les contraintes : budget, délai et interruption acceptable.
          </p>
        </div>
        <div className="cta-actions">
          <button className="btn btn-secondary" onClick={onRecommencer}><RotateCcw size={16} />Autre projet</button>
          <button className="btn btn-primary btn-lg" onClick={onCreerPlan}>
            <Sparkles size={18} />Créer le plan<ArrowRight size={16} />
          </button>
        </div>
      </section>

      <section className="card">
        <div className="liste-tete">
          <h2 className="section-title"><ShieldAlert size={18} />Problèmes détectés</h2>
          <div className="chips">
            {FILTRES.map((f) => (
              <button key={f} className={`chip ${filtre === f ? "active" : ""}`} onClick={() => setFiltre(f)}>{f}</button>
            ))}
          </div>
        </div>
        {problemes.length === 0 ? (
          <p className="muted">Aucun problème dans cette catégorie.</p>
        ) : (
          <div className="problemes">{problemes.map((p) => <ProblemeCarte key={p.regle + p.titre} probleme={p} />)}</div>
        )}
      </section>

      {resultat.dependances.length > 0 && (
        <details className="card dependances">
          <summary className="section-title"><Boxes size={18} />Dépendances ({resultat.dependances.length})</summary>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Nom</th><th>Version</th><th>Source</th></tr></thead>
              <tbody>
                {resultat.dependances.map((d) => (
                  <tr key={d.ecosysteme + d.nom}><td className="strong">{d.nom}</td><td>{d.version || "—"}</td><td className="muted">{d.ecosysteme}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </>
  );
}

export default function ScannerPage({ onCreerPlan }) {
  const [resultat, setResultat] = useState(null);
  const [nomFichier, setNomFichier] = useState("");
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState(null);
  const [survol, setSurvol] = useState(false);
  const champ = useRef(null);

  const analyser = async (fichier) => {
    if (!fichier) return;
    setErreur(null);
    if (!fichier.name.toLowerCase().endsWith(".zip")) {
      setErreur("Déposez une archive .zip du projet.");
      return;
    }
    if (fichier.size > TAILLE_MAX_MO * 1024 * 1024) {
      setErreur(`L'archive dépasse ${TAILLE_MAX_MO} Mo. Retirez les dossiers vendor, node_modules et les fichiers volumineux.`);
      return;
    }
    setNomFichier(fichier.name);
    setEnCours(true);
    try {
      setResultat(await api.analyserProjet(fichier));
    } catch (e) {
      setErreur(e.message);
    } finally {
      setEnCours(false);
    }
  };

  const deposer = (e) => {
    e.preventDefault();
    setSurvol(false);
    analyser(e.dataTransfer.files[0]);
  };

  const recommencer = () => {
    setResultat(null);
    setErreur(null);
    if (champ.current) champ.current.value = "";
  };

  return (
    <div className="page page-large">
      <header className="page-header">
        <div>
          <p className="eyebrow">Outils</p>
          <h1>Scanner de code</h1>
          <p className="subtitle">
            Déposez votre projet : MigraPlan détecte ses technologies, repère ce qui va casser
            pendant la migration et prépare le formulaire du plan.
          </p>
        </div>
      </header>

      {erreur && <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>}

      {!resultat && (
        <label
          className={`depot card ${survol ? "survol" : ""} ${enCours ? "en-cours" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setSurvol(true); }}
          onDragLeave={() => setSurvol(false)}
          onDrop={deposer}
        >
          <input
            ref={champ} type="file" accept=".zip,application/zip" hidden disabled={enCours}
            onChange={(e) => analyser(e.target.files[0])}
          />
          {enCours ? (
            <>
              <Loader2 size={40} className="spin" />
              <h2>Analyse de {nomFichier}…</h2>
              <p className="subtitle">Lecture des fichiers, détection des technologies et recherche des incompatibilités.</p>
            </>
          ) : (
            <>
              <span className="depot-icone"><UploadCloud size={30} /></span>
              <h2>Déposez l'archive .zip de votre projet</h2>
              <p className="subtitle">ou cliquez pour choisir un fichier</p>
              <div className="depot-langages">
                <span className="badge badge-outline">PHP</span>
                <span className="badge badge-outline">Java</span>
                <span className="badge badge-outline">Node.js</span>
                <span className="muted">· {TAILLE_MAX_MO} Mo maximum · vendor et node_modules ignorés</span>
              </div>
            </>
          )}
        </label>
      )}

      {!resultat && !enCours && (
        <p className="confidentialite">
          <Lock size={14} />
          Le code est analysé en mémoire puis oublié : rien n'est conservé. Les mots de passe trouvés sont masqués.
        </p>
      )}

      {resultat && (
        <Resultats
          resultat={resultat}
          nomFichier={nomFichier}
          onRecommencer={recommencer}
          onCreerPlan={() => onCreerPlan(resultat, nomFichier)}
        />
      )}
    </div>
  );
}
