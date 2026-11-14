import { Check } from "lucide-react";

// Affiche un champ du formulaire selon son type
export default function Field({ champ, valeur, erreur, onChange }) {
  const { name, label, type, required, options, placeholder, full } = champ;
  const id = `champ-${name}`;

  let controle;
  if (type === "select") {
    controle = (
      <select id={id} value={valeur} onChange={(e) => onChange(name, e.target.value)}>
        {!required || valeur === "" ? <option value="">Sélectionner…</option> : null}
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    );
  } else if (type === "multi") {
    const basculer = (o) =>
      onChange(name, valeur.includes(o) ? valeur.filter((v) => v !== o) : [...valeur, o]);
    controle = (
      <div className="chips" role="group" aria-labelledby={id}>
        {options.map((o) => {
          const actif = valeur.includes(o);
          return (
            <button
              type="button"
              key={o}
              className={`chip ${actif ? "active" : ""}`}
              aria-pressed={actif}
              onClick={() => basculer(o)}
            >
              {actif && <Check size={14} />}
              {o}
            </button>
          );
        })}
      </div>
    );
  } else if (type === "textarea") {
    controle = (
      <textarea id={id} rows={4} value={valeur} placeholder={placeholder}
        onChange={(e) => onChange(name, e.target.value)} />
    );
  } else {
    controle = (
      <input id={id} type={type} min={type === "number" ? 1 : undefined} value={valeur}
        placeholder={placeholder} onChange={(e) => onChange(name, e.target.value)} />
    );
  }

  return (
    <div className={`field ${full ? "full" : ""} ${erreur ? "has-error" : ""}`}>
      <label htmlFor={id} id={type === "multi" ? id : undefined}>
        {label} {required && <span className="required">*</span>}
      </label>
      {controle}
      {erreur && <span className="field-error">{erreur}</span>}
    </div>
  );
}
