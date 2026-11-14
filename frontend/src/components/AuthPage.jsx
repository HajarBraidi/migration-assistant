import { useState } from "react";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import Logo from "./Logo.jsx";
import { api } from "../api.js";

const ATOUTS = [
  "Stratégie de migration recommandée selon le modèle des 7R",
  "Plan complet en 8 sections : phases, risques, rollback, estimation",
  "Vérification automatique de la cohérence avec vos contraintes",
];

export default function AuthPage({ onConnecte }) {
  const [mode, setMode] = useState("login"); // "login" ou "register"
  const [valeurs, setValeurs] = useState({ nom: "", email: "", mot_de_passe: "" });
  const [erreur, setErreur] = useState(null);
  const [envoi, setEnvoi] = useState(false);

  const inscription = mode === "register";
  const modifier = (e) => setValeurs((v) => ({ ...v, [e.target.name]: e.target.value }));

  const changerMode = () => {
    setMode(inscription ? "login" : "register");
    setErreur(null);
  };

  const soumettre = async (e) => {
    e.preventDefault();
    setErreur(null);
    if (inscription && valeurs.mot_de_passe.length < 8) {
      setErreur("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    setEnvoi(true);
    try {
      const session = inscription
        ? await api.inscrire(valeurs)
        : await api.connecter({ email: valeurs.email, mot_de_passe: valeurs.mot_de_passe });
      onConnecte(session);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setEnvoi(false);
    }
  };

  return (
    <div className="auth">
      <aside className="auth-panel">
        <div className="brand">
          <Logo taille={40} />
          <div>
            <div className="brand-name">MigraPlan</div>
            <div className="brand-tagline">Assistant de migration</div>
          </div>
        </div>
        <div className="auth-pitch">
          <h1>Planifiez la migration de vos applications avec l'IA générative.</h1>
          <ul>
            {ATOUTS.map((a) => (
              <li key={a}><CheckCircle2 size={18} />{a}</li>
            ))}
          </ul>
        </div>
        
      </aside>

      <main className="auth-main">
        <form className="auth-form" onSubmit={soumettre}>
          <h2>{inscription ? "Créer un compte" : "Connexion"}</h2>
          <p className="subtitle">
            {inscription
              ? "Quelques secondes suffisent pour commencer."
              : "Accédez à vos plans de migration."}
          </p>

          {erreur && (
            <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>
          )}

          {inscription && (
            <div className="field">
              <label htmlFor="nom">Nom complet</label>
              <input id="nom" name="nom" value={valeurs.nom} onChange={modifier} required autoComplete="name" />
            </div>
          )}
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" name="email" type="email" value={valeurs.email} onChange={modifier} required autoComplete="email" />
          </div>
          <div className="field">
            <label htmlFor="mot_de_passe">Mot de passe</label>
            <input
              id="mot_de_passe" name="mot_de_passe" type="password" value={valeurs.mot_de_passe}
              onChange={modifier} required autoComplete={inscription ? "new-password" : "current-password"}
            />
            {inscription && <span className="hint">8 caractères minimum.</span>}
          </div>

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={envoi}>
            {envoi && <Loader2 size={18} className="spin" />}
            {inscription ? "Créer mon compte" : "Se connecter"}
          </button>

          <p className="auth-switch">
            {inscription ? "Déjà un compte ?" : "Pas encore de compte ?"}{" "}
            <button type="button" className="link" onClick={changerMode}>
              {inscription ? "Se connecter" : "Créer un compte"}
            </button>
          </p>
        </form>
      </main>
    </div>
  );
}
