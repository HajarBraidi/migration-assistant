import { useEffect, useState } from "react";
import { AlertCircle, ExternalLink, Info, Loader2 } from "lucide-react";
import { api } from "../api.js";

const formater = (montant, devise) =>
  new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: devise,
    maximumFractionDigits: montant < 100 ? 2 : 0,
  }).format(montant);

// Compare le coût mensuel d'hébergement chez les fournisseurs cloud
export default function CostComparison({ demande, cible }) {
  const [estimation, setEstimation] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [devise, setDevise] = useState("EUR");
  const [detail, setDetail] = useState(null);
  const cle = JSON.stringify(demande);

  useEffect(() => {
    let actif = true;
    setErreur(null);
    api.estimerCouts(demande)
      .then((resultat) => {
        if (!actif) return;
        setEstimation(resultat);
        setDetail((d) => d || resultat.moins_chere);
      })
      .catch((e) => actif && setErreur(e.message));
    return () => {
      actif = false;
    };
  }, [cle]); // eslint-disable-line react-hooks/exhaustive-deps

  if (erreur) return <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>;
  if (!estimation) return <div className="cout-chargement"><Loader2 size={18} className="spin" />Calcul des coûts…</div>;

  const taux = devise === "MAD" ? estimation.eur_vers_mad : 1;
  const prix = (eur) => formater(eur * taux, devise);
  const maximum = Math.max(...estimation.offres.map((o) => o.total_mensuel_eur));
  const d = estimation.dimensionnement;
  const offreDetail = estimation.offres.find((o) => o.fournisseur === detail) || estimation.offres[0];

  return (
    <div className="couts">
      <div className="couts-tete">
        <p className="couts-hypotheses">
          <strong>Hypothèses :</strong> {d.serveurs} serveur{d.serveurs > 1 ? "s" : ""} ({d.description_taille})
          · base {d.base_de_donnees}{d.instances_base > 1 ? " répliquée" : ""} · {d.stockage_go} Go de données
          · {d.trafic_sortant_go} Go de trafic sortant par mois
          {d.repartiteur_de_charge ? " · répartiteur de charge" : ""}
        </p>
        <div className="segment" role="group" aria-label="Devise">
          {["EUR", "MAD"].map((code) => (
            <button key={code} className={devise === code ? "actif" : ""} onClick={() => setDevise(code)}>
              {code === "EUR" ? "€" : "MAD"}
            </button>
          ))}
        </div>
      </div>

      {/* Graphique : coût mensuel par fournisseur (une seule série, une seule couleur) */}
      <div className="barres" role="list">
        {estimation.offres.map((o) => (
          <button
            key={o.fournisseur}
            role="listitem"
            className={`barre-ligne ${detail === o.fournisseur ? "selectionnee" : ""}`}
            onClick={() => setDetail(o.fournisseur)}
            title={`${o.nom} — ${prix(o.total_mensuel_eur)} par mois, ${prix(o.total_annuel_eur)} par an`}
          >
            <span className="barre-nom">
              {o.nom}
              <span className="barre-gestion">{o.gestion}</span>
            </span>
            <span className="barre-piste">
              <span className="barre" style={{ width: `${Math.max(2, (o.total_mensuel_eur / maximum) * 100)}%` }} />
            </span>
            <span className="barre-valeur">
              {prix(o.total_mensuel_eur)}<span className="muted"> / mois</span>
            </span>
            <span className="barre-tags">
              {o.fournisseur === estimation.moins_chere && <span className="badge badge-low">Le moins cher</span>}
              {o.fournisseur === cible && <span className="badge badge-primary">Votre choix</span>}
            </span>
          </button>
        ))}
      </div>

      <div className="couts-detail">
        <div className="couts-detail-tete">
          <h3>Détail — {offreDetail.nom} <span className="muted">({offreDetail.region})</span></h3>
          <a href={offreDetail.calculateur} target="_blank" rel="noreferrer" className="lien-externe">
            Vérifier sur le calculateur officiel <ExternalLink size={14} />
          </a>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Poste</th><th>Détail</th><th className="align-right">Par mois</th></tr></thead>
            <tbody>
              {offreDetail.lignes.map((l) => (
                <tr key={l.poste}>
                  <td className="strong">{l.poste}</td>
                  <td className="muted">{l.detail}</td>
                  <td className="align-right nombre">{l.prix_texte || prix(l.cout_mensuel_eur)}</td>
                </tr>
              ))}
              <tr className="total">
                <td colSpan={2}>Total ({prix(offreDetail.total_annuel_eur)} par an)</td>
                <td className="align-right nombre">{prix(offreDetail.total_mensuel_eur)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {estimation.remarques.length > 0 && (
        <ul className="couts-remarques">
          {estimation.remarques.map((r) => <li key={r}><Info size={16} />{r}</li>)}
        </ul>
      )}

      <p className="couts-avertissement">
        Tarifs publics à la demande (sans engagement) relevés en {estimation.releve_le}, hors taxes,
        régions européennes{devise === "MAD" ? `, conversion indicative 1 € = ${estimation.eur_vers_mad} MAD` : ""}.
        Ce sont des ordres de grandeur pour comparer : vérifiez avec le calculateur officiel avant de décider.
      </p>
    </div>
  );
}
