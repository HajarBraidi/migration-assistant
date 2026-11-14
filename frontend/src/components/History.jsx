import { useEffect, useState } from "react";
import { AlertCircle, ChevronRight, FolderOpen, Loader2 } from "lucide-react";
import { api } from "../api.js";

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

export default function History({ onOuvrir, onNouveau }) {
  const [projets, setProjets] = useState(null);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    api.listerProjets().then(setProjets).catch((e) => setErreur(e.message));
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Historique</p>
          <h1>Plans de migration</h1>
          <p className="subtitle">Retrouvez les plans générés précédemment.</p>
        </div>
      </header>

      {erreur && <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>}

      {!erreur && projets === null && (
        <div className="card empty"><Loader2 className="spin" size={24} /><p>Chargement…</p></div>
      )}

      {projets?.length === 0 && (
        <div className="card empty">
          <FolderOpen size={32} />
          <h2>Aucun plan pour le moment</h2>
          <p className="subtitle">Décrivez une application pour générer votre premier plan.</p>
          <button className="btn btn-primary" onClick={onNouveau}>Nouvelle analyse</button>
        </div>
      )}

      {projets?.length > 0 && (
        <div className="card table-card">
          <table>
            <thead><tr><th>Application</th><th>Stratégie</th><th>Date</th><th aria-label="Ouvrir" /></tr></thead>
            <tbody>
              {projets.map((p) => (
                <tr key={p.id} className="clickable" onClick={() => onOuvrir(p.id)}>
                  <td className="strong">{p.nom}</td>
                  <td><span className="badge badge-primary">{p.strategie}</span></td>
                  <td className="muted">{formatDate(p.cree_le)}</td>
                  <td className="align-right"><ChevronRight size={18} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
