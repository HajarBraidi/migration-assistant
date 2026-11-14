import { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import MigrationForm from "./components/MigrationForm.jsx";
import Loader from "./components/Loader.jsx";
import PlanView from "./components/PlanView.jsx";
import History from "./components/History.jsx";
import { api } from "./api.js";
import { VALEURS_INITIALES } from "./formConfig.js";

export default function App() {
  // Vues possibles : "form", "loading", "plan", "history"
  const [vue, setVue] = useState("form");
  const [projet, setProjet] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [valeurs, setValeurs] = useState(VALEURS_INITIALES);

  const naviguer = (nouvelleVue) => {
    setErreur(null);
    setVue(nouvelleVue);
    window.scrollTo(0, 0);
  };

  const generer = async (description) => {
    setErreur(null);
    setVue("loading");
    try {
      setProjet(await api.creerProjet(description));
      naviguer("plan");
    } catch (e) {
      setErreur(e.message);
      setVue("form");
    }
  };

  const ouvrir = async (id) => {
    try {
      setProjet(await api.obtenirProjet(id));
      naviguer("plan");
    } catch (e) {
      setErreur(e.message);
    }
  };

  return (
    <div className="layout">
      <Sidebar vue={vue === "plan" ? "history" : vue} onNaviguer={naviguer} />
      <main className="content">
        {vue === "form" && <MigrationForm valeurs={valeurs} setValeurs={setValeurs} onSoumettre={generer} erreurServeur={erreur} />}
        {vue === "loading" && <Loader />}
        {vue === "plan" && projet && <PlanView projet={projet} onRetour={() => naviguer("history")} />}
        {vue === "history" && <History onOuvrir={ouvrir} onNouveau={() => naviguer("form")} />}
      </main>
    </div>
  );
}
