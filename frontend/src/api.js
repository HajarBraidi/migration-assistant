// Toutes les requêtes passent par l'api-gateway (préfixe /api)

const CLE_SESSION = "migraplan.session";

const LIBELLES_CHAMPS = {
  nom: "Nom",
  email: "Email",
  mot_de_passe: "Mot de passe",
  message: "Message",
  objectifs: "Objectifs de la migration",
  taille_equipe: "Taille de l'équipe",
};

// ---------- Session (jeton + utilisateur), conservée dans le navigateur ----------

export function lireSession() {
  try {
    return JSON.parse(localStorage.getItem(CLE_SESSION));
  } catch {
    return null;
  }
}

function enregistrerSession(session) {
  try {
    localStorage.setItem(CLE_SESSION, JSON.stringify(session));
  } catch {
    /* stockage indisponible : la session durera le temps de l'onglet */
  }
}

export function effacerSession() {
  try {
    localStorage.removeItem(CLE_SESSION);
  } catch {
    /* rien à faire */
  }
}

// Appelée quand le serveur répond 401 (jeton absent, invalide ou expiré)
let surSessionExpiree = () => {};
export function quandSessionExpiree(fonction) {
  surSessionExpiree = fonction;
}

// ---------- Requêtes ----------

function messageErreur(status, data) {
  if (status === 422 && Array.isArray(data?.detail)) {
    const champs = data.detail.map((e) => {
      const champ = e.loc?.[e.loc.length - 1];
      return LIBELLES_CHAMPS[champ] || champ;
    });
    return `Certaines informations sont invalides : ${[...new Set(champs)].join(", ")}.`;
  }
  if (status === 502 || status === 503) {
    return "Le service est momentanément indisponible. Réessayez dans quelques instants.";
  }
  if (status === 404) return "Ce projet est introuvable.";
  if (status === 413) return data?.detail || "Le fichier est trop volumineux.";
  return data?.detail || "Une erreur inattendue est survenue.";
}

async function requete(chemin, options = {}) {
  const session = lireSession();
  let reponse;
  try {
    // Pour un envoi de fichier (FormData), le navigateur choisit lui-même le Content-Type
    const estFichier = options.body instanceof FormData;
    reponse = await fetch(`/api${chemin}`, {
      ...options,
      headers: {
        ...(estFichier ? {} : { "Content-Type": "application/json" }),
        ...(session ? { Authorization: `Bearer ${session.jeton}` } : {}),
      },
    });
  } catch {
    throw new Error("Impossible de joindre le serveur. Vérifiez que l'application est démarrée.");
  }
  const data = await reponse.json().catch(() => null);
  if (reponse.status === 401 && session && !chemin.startsWith("/auth/login")) {
    effacerSession();
    surSessionExpiree();
  }
  if (!reponse.ok) {
    const erreur = new Error(messageErreur(reponse.status, data));
    erreur.status = reponse.status;
    throw erreur;
  }
  return data;
}

async function authentifier(chemin, donnees) {
  const data = await requete(chemin, { method: "POST", body: JSON.stringify(donnees) });
  const session = { jeton: data.access_token, utilisateur: data.utilisateur };
  enregistrerSession(session);
  return session;
}

function formulaireFichier(fichier) {
  const donnees = new FormData();
  donnees.append("archive", fichier);
  return donnees;
}

// Téléchargement d'un fichier renvoyé par le serveur (archive du kit)
async function telecharger(chemin, donnees, nomParDefaut) {
  const session = lireSession();
  let reponse;
  try {
    reponse = await fetch(`/api${chemin}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(session ? { Authorization: `Bearer ${session.jeton}` } : {}),
      },
      body: JSON.stringify(donnees),
    });
  } catch {
    throw new Error("Impossible de joindre le serveur. Vérifiez que l'application est démarrée.");
  }
  if (!reponse.ok) {
    const data = await reponse.json().catch(() => null);
    throw new Error(messageErreur(reponse.status, data));
  }
  const nom =
    /filename="([^"]+)"/.exec(reponse.headers.get("content-disposition") || "")?.[1] || nomParDefaut;
  const url = URL.createObjectURL(await reponse.blob());
  const lien = document.createElement("a");
  lien.href = url;
  lien.download = nom;
  document.body.appendChild(lien);
  lien.click();
  lien.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const api = {
  apercuKit: (demande) => requete("/kits", { method: "POST", body: JSON.stringify(demande) }),
  telechargerKit: (demande) => telecharger("/kits/archive", demande, "kit-deploiement.zip"),
  estimerCouts: (demande) =>
    requete("/estimations", { method: "POST", body: JSON.stringify(demande) }),
  analyserProjet: (fichier) =>
    requete("/analyses", { method: "POST", body: formulaireFichier(fichier) }),
  inscrire: (donnees) => authentifier("/auth/register", donnees),
  connecter: (donnees) => authentifier("/auth/login", donnees),
  moi: () => requete("/auth/me"),
  creerProjet: (description) =>
    requete("/projects", { method: "POST", body: JSON.stringify(description) }),
  listerProjets: () => requete("/projects"),
  obtenirProjet: (id) => requete(`/projects/${id}`),
  envoyerMessage: (id, message) =>
    requete(`/projects/${id}/messages`, { method: "POST", body: JSON.stringify({ message }) }),
  obtenirVersion: (id, numero) => requete(`/projects/${id}/versions/${numero}`),
  restaurerVersion: (id, numero) =>
    requete(`/projects/${id}/versions/${numero}/restaurer`, { method: "POST" }),
};
