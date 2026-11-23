import { useState } from "react";
import { AlertCircle, ArrowDown, CheckCircle2, ScanSearch, Sparkles, Wand2 } from "lucide-react";
import Field from "./Field.jsx";
import { EXEMPLE_STOCKPRO, SECTIONS, valider, versDescription } from "../formConfig.js";

// Les valeurs sont gardées dans App : elles ne sont pas perdues en cas d'erreur
export default function MigrationForm({ valeurs, setValeurs, onSoumettre, erreurServeur, preRempli }) {
  const [erreurs, setErreurs] = useState({});

  // Champs modifiés par l'utilisateur : leur étiquette « Détecté / À vérifier » disparaît
  const [confirmes, setConfirmes] = useState(new Set());
  const manquants = preRempli ? Object.keys(valider(valeurs)) : [];

  const origine = (nom) => {
    if (!preRempli || confirmes.has(nom)) return null;
    if (preRempli.aVerifier.includes(nom)) return "verifier";
    if (preRempli.detectes.includes(nom)) return "detecte";
    return null;
  };

  const allerAuPremierManquant = () =>
    document.querySelector(".a-completer")?.scrollIntoView({ behavior: "smooth", block: "center" });

  const modifier = (nom, valeur) => {
    setConfirmes((c) => new Set(c).add(nom));
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
        <button type="button" className="btn btn-secondary" onClick={() => { setValeurs(EXEMPLE_STOCKPRO); setErreurs({}); setConfirmes(new Set()); }}>
          <Wand2 size={16} />
          Remplir avec un exemple
        </button>
      </header>

      {preRempli && (
        <div className="alert alert-info prerempli">
          <ScanSearch size={18} />
          <div className="alert-body">
            <span>
              Formulaire pré-rempli à partir de l'analyse de <strong>{preRempli.fichier}</strong> :{" "}
              <strong>{preRempli.detectes.length}</strong> champs détectés dans le code,{" "}
              <strong>{preRempli.aVerifier.length}</strong> déduits d'indices (à vérifier).
            </span>
            {manquants.length > 0 ? (
              <div className="alert-actions">
                <span className="reste">
                  Il reste <strong>{manquants.length}</strong> champ{manquants.length > 1 ? "s" : ""} obligatoire
                  {manquants.length > 1 ? "s" : ""} à compléter.
                </span>
                <button type="button" className="btn btn-primary btn-sm" onClick={allerAuPremierManquant}>
                  <ArrowDown size={14} />Compléter
                </button>
              </div>
            ) : (
              <span className="reste-ok">
                <CheckCircle2 size={16} /> Tous les champs obligatoires sont remplis : vérifiez les
                champs « À vérifier », puis générez le plan.
              </span>
            )}
          </div>
        </div>
      )}

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
                erreur={erreurs[champ.name]} onChange={modifier}
                origine={origine(champ.name)} aCompleter={manquants.includes(champ.name)} />
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
