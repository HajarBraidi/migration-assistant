import { useState } from "react";
import { AlertCircle, Sparkles, Wand2 } from "lucide-react";
import Field from "./Field.jsx";
import { EXEMPLE_STOCKPRO, SECTIONS, valider, versDescription } from "../formConfig.js";

// Les valeurs sont gardées dans App : elles ne sont pas perdues en cas d'erreur
export default function MigrationForm({ valeurs, setValeurs, onSoumettre, erreurServeur }) {
  const [erreurs, setErreurs] = useState({});

  const modifier = (nom, valeur) => {
    setValeurs((v) => ({ ...v, [nom]: valeur }));
    setErreurs((e) => ({ ...e, [nom]: undefined }));
  };

  const soumettre = (evenement) => {
    evenement.preventDefault();
    const nouvellesErreurs = valider(valeurs);
    setErreurs(nouvellesErreurs);
    if (Object.keys(nouvellesErreurs).length > 0) {
      document.querySelector(".has-error")?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    onSoumettre(versDescription(valeurs));
  };

  return (
    <form className="page" onSubmit={soumettre} noValidate>
      <header className="page-header">
        <div>
          <p className="eyebrow">Nouvelle analyse</p>
          <h1>Décrivez votre application</h1>
          <p className="subtitle">
            Renseignez l'existant et vos contraintes. L'assistant recommande une stratégie
            de migration et génère un plan complet.
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={() => { setValeurs(EXEMPLE_STOCKPRO); setErreurs({}); }}>
          <Wand2 size={16} />
          Remplir avec un exemple
        </button>
      </header>

      {erreurServeur && (
        <div className="alert alert-error">
          <AlertCircle size={18} />
          <span>{erreurServeur}</span>
        </div>
      )}

      {SECTIONS.map((section, index) => (
        <section key={section.id} className="card">
          <div className="card-header">
            <span className="step">{index + 1}</span>
            <div>
              <h2>{section.titre}</h2>
              <p>{section.description}</p>
            </div>
          </div>
          <div className="grid">
            {section.champs.map((champ) => (
              <Field key={champ.name} champ={champ} valeur={valeurs[champ.name]}
                erreur={erreurs[champ.name]} onChange={modifier} />
            ))}
          </div>
        </section>
      ))}

      <div className="form-actions">
        <span className="hint"><span className="required">*</span> Champs obligatoires</span>
        <button type="submit" className="btn btn-primary btn-lg">
          <Sparkles size={18} />
          Générer le plan de migration
        </button>
      </div>
    </form>
  );
}
