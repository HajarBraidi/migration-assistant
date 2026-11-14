import { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";

const ETAPES = [
  "Analyse de la description",
  "Choix de la stratégie de migration",
  "Rédaction du plan détaillé",
  "Vérification de la cohérence",
];

export default function Loader() {
  const [etape, setEtape] = useState(0);

  useEffect(() => {
    const minuteur = setInterval(() => setEtape((e) => Math.min(e + 1, ETAPES.length - 1)), 4000);
    return () => clearInterval(minuteur);
  }, []);

  return (
    <div className="page loader-page">
      <div className="card loader-card">
        <Loader2 className="spin" size={36} />
        <h2>Génération du plan en cours</h2>
        <p className="subtitle">Cette opération prend généralement entre 10 et 40 secondes.</p>
        <ul className="loader-steps">
          {ETAPES.map((libelle, i) => (
            <li key={libelle} className={i < etape ? "done" : i === etape ? "current" : ""}>
              <span className="dot">{i < etape ? <Check size={12} /> : null}</span>
              {libelle}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
