import { useState } from "react";
import { Calculator } from "lucide-react";
import CostComparison from "./CostComparison.jsx";
import { SECTIONS } from "../formConfig.js";

const options = (nom) => SECTIONS.flatMap((s) => s.champs).find((c) => c.name === nom).options;

export default function CostPage() {
  const [besoins, setBesoins] = useState({
    nombre_utilisateurs: "100 à 1 000",
    volume_donnees: "10 à 100 Go",
    type_base_donnees: "MySQL",
    haute_disponibilite: false,
  });
  const modifier = (nom, valeur) => setBesoins((b) => ({ ...b, [nom]: valeur }));

  return (
    <div className="page page-large">
      <header className="page-header">
        <div>
          <p className="eyebrow">Outils</p>
          <h1>Comparateur de coûts</h1>
          <p className="subtitle">
            Estimez le coût mensuel d'hébergement de votre application chez AWS, Azure,
            Google Cloud et OVHcloud, à partir de vos besoins.
          </p>
        </div>
      </header>

      <section className="card">
        <h2 className="section-title"><Calculator size={18} />Vos besoins</h2>
        <div className="grid grid-4">
          <div className="field">
            <label htmlFor="cout-utilisateurs">Nombre d'utilisateurs</label>
            <select id="cout-utilisateurs" value={besoins.nombre_utilisateurs} onChange={(e) => modifier("nombre_utilisateurs", e.target.value)}>
              {options("nombre_utilisateurs").map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="cout-volume">Volume des données</label>
            <select id="cout-volume" value={besoins.volume_donnees} onChange={(e) => modifier("volume_donnees", e.target.value)}>
              {options("volume_donnees").map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="cout-base">Base de données</label>
            <select id="cout-base" value={besoins.type_base_donnees} onChange={(e) => modifier("type_base_donnees", e.target.value)}>
              {options("type_base_donnees").filter((o) => o !== "Autre").map((o) => <option key={o}>{o}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="cout-dispo">Disponibilité</label>
            <select
              id="cout-dispo"
              value={besoins.haute_disponibilite ? "haute" : "standard"}
              onChange={(e) => modifier("haute_disponibilite", e.target.value === "haute")}
            >
              <option value="standard">Standard (coupures courtes acceptées)</option>
              <option value="haute">Haute (aucune interruption)</option>
            </select>
          </div>
        </div>
      </section>

      <section className="card">
        <CostComparison demande={besoins} />
      </section>
    </div>
  );
}
