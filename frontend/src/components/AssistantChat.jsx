import { useEffect, useRef, useState } from "react";
import { AlertCircle, Bot, Loader2, Send } from "lucide-react";
import { api } from "../api.js";

const SUGGESTIONS = [
  "Pourquoi cette stratégie ?",
  "Peut-on réduire le coût ?",
  "Peut-on migrer sans interruption de service ?",
  "Je préfère un hébergement sur AWS",
];

const ETIQUETTES = {
  question: { texte: "Question", classe: "badge-medium" },
  reponse: { texte: "Explication", classe: "badge-neutral" },
};

function Bulle({ message }) {
  const assistant = message.role === "assistant";
  const etiquette = message.version_creee
    ? { texte: `Nouvelle version V${message.version_creee}`, classe: "badge-primary" }
    : ETIQUETTES[message.type];

  return (
    <div className={`bulle ${assistant ? "bulle-assistant" : "bulle-utilisateur"}`}>
      {assistant && etiquette && <span className={`badge ${etiquette.classe}`}>{etiquette.texte}</span>}
      <p>{message.contenu}</p>
    </div>
  );
}

export default function AssistantChat({ projet, onMiseAJour, lectureSeule = false }) {
  const [texte, setTexte] = useState("");
  const [enAttente, setEnAttente] = useState(null); // message envoyé, en attente de réponse
  const [erreur, setErreur] = useState(null);
  const finRef = useRef(null);

  const messages = enAttente
    ? [...projet.messages, { id: "attente", role: "utilisateur", contenu: enAttente }]
    : projet.messages;

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [messages.length, enAttente]);

  const envoyer = async (contenu) => {
    const message = contenu.trim();
    if (!message || enAttente || lectureSeule) return;
    setErreur(null);
    setEnAttente(message);
    setTexte("");
    try {
      onMiseAJour(await api.envoyerMessage(projet.id, message));
    } catch (err) {
      setErreur(err.message);
      setTexte(message); // on rend le texte pour pouvoir réessayer
    } finally {
      setEnAttente(null);
    }
  };

  const toucheClavier = (e) => {
    // Entrée envoie, Maj + Entrée ajoute une ligne
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      envoyer(texte);
    }
  };

  return (
    <section className="card chat no-print">
      <h2 className="section-title"><Bot size={18} />Discuter avec l'assistant</h2>

      <div className="chat-messages">
        <div className="bulle bulle-assistant">
          <p>
            Bonjour ! Je peux vous expliquer ce plan, répondre à vos questions ou l'ajuster.
            Je ne crée une nouvelle version que lorsqu'une modification est décidée ;
            les versions précédentes restent consultables.
          </p>
        </div>
        {messages.map((m) => <Bulle key={m.id} message={m} />)}
        {enAttente && (
          <div className="bulle bulle-assistant bulle-attente">
            <Loader2 size={16} className="spin" /> L'assistant réfléchit…
          </div>
        )}
        <div ref={finRef} />
      </div>

      {lectureSeule && (
        <p className="chat-note">
          Vous consultez une ancienne version. Revenez à la version actuelle pour discuter.
        </p>
      )}

      {projet.messages.length === 0 && !enAttente && !lectureSeule && (
        <div className="chips">
          {SUGGESTIONS.map((s) => (
            <button key={s} type="button" className="chip" onClick={() => envoyer(s)}>{s}</button>
          ))}
        </div>
      )}

      {erreur && <div className="alert alert-error"><AlertCircle size={18} /><span>{erreur}</span></div>}

      <form className="chat-form" onSubmit={(e) => { e.preventDefault(); envoyer(texte); }}>
        <textarea
          rows={2}
          maxLength={1000}
          value={texte}
          disabled={Boolean(enAttente) || lectureSeule}
          placeholder="Votre message… (Entrée pour envoyer)"
          onChange={(e) => setTexte(e.target.value)}
          onKeyDown={toucheClavier}
        />
        <button type="submit" className="btn btn-primary" disabled={Boolean(enAttente) || lectureSeule || !texte.trim()} aria-label="Envoyer">
          <Send size={16} />
        </button>
      </form>
    </section>
  );
}
