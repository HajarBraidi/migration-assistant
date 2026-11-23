import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import MigrationForm from "./components/MigrationForm.jsx";
import Loader from "./components/Loader.jsx";
import PlanView from "./components/PlanView.jsx";
import History from "./components/History.jsx";
import AuthPage from "./components/AuthPage.jsx";
import ScannerPage from "./components/ScannerPage.jsx";
import { api, effacerSession, lireSession, quandSessionExpiree } from "./api.js";
import { VALEURS_INITIALES } from "./formConfig.js";

export default function App() {
  const [session, setSession] = useState(lireSession);
  // Vues possibles : "form", "loading", "plan", "history", "scanner"
  const [vue, setVue] = useState("form");
  const [projet, setProjet] = useState(null);
  const [erreur, setErreur] = useState(null);
  const [valeurs, setValeurs] = useState(VALEURS_INITIALES);
  // Pré-remplissage par le scanner : { fichier, detectes, aVerifier }
  const [preRempli, setPreRempli] = useState(null);

  const deconnecter = () => {
    effacerSession();
    setSession(null);
    setProjet(null);
    setValeurs(VALEURS_INITIALES);
    setPreRempli(null);
    setVue("form");
  };

  useEffect(() => {
    // Si le jeton expire pendant l'utilisation, on revient à la page de connexion
    quandSessionExpiree(() => setSession(null));
    // Au démarrage, on vérifie que la session enregistrée est toujours valide
    if (lireSession()) api.moi().catch(() => {});
  }, []);

  if (!session) return <AuthPage onConnecte={setSession} />;

  const naviguer = (nouvelleVue) => {
    setErreur(null);
    setVue(nouvelleVue);
    window.scrollTo(0, 0);
  };

  // Le scanner pré-remplit le formulaire puis affiche la page « Nouvelle analyse »
  const creerPlanDepuisAnalyse = (resultat, nomFichier) => {
    const nom = nomFichier.replace(/\.zip$/i, "").replace(/[-_]+/g, " ").slice(0, 100);
    setValeurs({ ...VALEURS_INITIALES, nom, ...resultat.description_preremplie });
    setPreRempli({
      fichier: nomFichier,
      detectes: resultat.champs_detectes,
      aVerifier: [...resultat.champs_a_verifier, "nom"],
    });
    naviguer("form");
  };

  const generer = async (description) => {
    setErreur(null);
    setVue("loading");
    try {
      setProjet(await api.creerProjet(description));
      setPreRempli(null);
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
      <Sidebar
        vue={vue === "plan" ? "history" : vue}
        onNaviguer={naviguer}
        utilisateur={session.utilisateur}
        onDeconnecter={deconnecter}
      />
      <main className="content">
        {vue === "form" && (
          <MigrationForm
            valeurs={valeurs}
            setValeurs={setValeurs}
            onSoumettre={generer}
            erreurServeur={erreur}
            preRempli={preRempli}
          />
        )}
        {vue === "loading" && <Loader />}
        {vue === "plan" && projet && <PlanView projet={projet} onRetour={() => naviguer("history")} onMiseAJour={setProjet} />}
        {vue === "history" && <History onOuvrir={ouvrir} onNouveau={() => naviguer("form")} />}
        {vue === "scanner" && <ScannerPage onCreerPlan={creerPlanDepuisAnalyse} />}
      </main>
    </div>
  );
}
