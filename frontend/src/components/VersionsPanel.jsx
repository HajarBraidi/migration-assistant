import { GitBranch } from "lucide-react";

const formatDate = (iso) =>
  new Date(iso).toLocaleString("fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export default function VersionsPanel({ versions, numeroAffiche, onVoir }) {
  const derniere = versions.length;

  return (
    <section className="card versions-card no-print">
      <h2 className="section-title"><GitBranch size={18} />Versions du plan</h2>
      <ol className="versions">
        {[...versions].reverse().map((v) => {
          const affichee = v.numero === numeroAffiche;
          return (
            <li key={v.numero} className={affichee ? "affichee" : ""}>
              <span className="version-num">V{v.numero}</span>
              <span className="version-origine">{v.origine}</span>
              <span className="muted">{formatDate(v.cree_le)}</span>
              {affichee ? (
                <span className="badge badge-primary">{v.numero === derniere ? "Actuelle" : "Affichée"}</span>
              ) : (
                <button className="btn btn-secondary btn-sm" onClick={() => onVoir(v.numero)}>Voir</button>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
