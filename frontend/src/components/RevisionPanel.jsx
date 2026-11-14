import { useState } from "react";
import { AlertCircle, Loader2, MessageSquareText, Send } from "lucide-react";
import { api } from "../api.js";

const SUGGESTIONS = [
  "Propose une option moins chère",
  "Réduis la durée de la migration",
  "Aucune interruption de service n'est possible",
  "Je préfère un hébergement sur AWS",
];

const formatDate = (iso) =>
  new Date(iso).toLocaleString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export default function RevisionPanel({ projet, onMiseAJour }) {
  const [demande, setDemande] = useState("");
  const [envoi, setEnvoi] = useState(false);
  const [erreur, setErreur] = useState(null);
  const revisions = projet.revisions || [];

  const envoyer = async (e) => {
    e.preventDefault();
    if (demande.trim().length < 3) {
      setErreur("Décrivez la modification souhaitée (3 caractères minimum).");
      return;
    }
    setErreur(null);
    setEnvoi(true);
    try {
      onMiseAJour(await api.reviserProjet(projet.id, demande.trim()));
      setDemande("");
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <section className="card revision no-print">
      <h2 className="section-title"><MessageSquareText size={18} />Ajuster le plan avec l'assistant</h2>
      <p className="subtitle">
        Demandez une modification : l'assistant produit une nouvelle version complète du plan,
        vérifiée par les règles de cohérence.
      </p>

      {revisions.length > 0 && (
        <ol className="versions">
          <li><span className="version-num">V1</span><span>Plan initial</span></li>
          {revisions.map((r, i) => (
            <li key={r.id}>
              <span className="version-num">V{i + 2}</span>
              <span className="version-demande">« {r.demande} »</span>
              <span className="muted">{formatDate(r.cree_le)}</span>
            </li>
          ))}
        </ol>
      )}

      <div className="chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" className="chip" disabled={envoi} onClick={() => setDemande(s)}>
            {s}
          </button>
        ))}
      </div>

      <form className="revision-form" onSubmit={envoyer}>
        <textarea
          rows={2}
          maxLength={500}
          value={demande}
          disabled={envoi}
          placeholder="Ex. Remplace MySQL par PostgreSQL et garde le même délai"
          onChange={(e) => setDemande(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={envoi}>
          {envoi ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
          {envoi ? "Ajustement en cours…" : "Appliquer"}
        </button>
      </form>

      {erreur && <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>}
    </section>
  );
}
