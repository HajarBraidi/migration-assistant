// Toutes les requêtes passent par l'api-gateway (préfixe /api)

const LIBELLES_CHAMPS = {
  nom: "Nom de l'application",
  objectifs: "Objectifs de la migration",
  taille_equipe: "Taille de l'équipe",
};

function messageErreur(status, data) {
  if (status === 422 && Array.isArray(data?.detail)) {
    const champs = data.detail.map((e) => {
      const champ = e.loc?.[e.loc.length - 1];
      return LIBELLES_CHAMPS[champ] || champ;
    });
    return `Certaines informations sont invalides : ${[...new Set(champs)].join(", ")}.`;
  }
  if (status === 502 || status === 503) {
    return "Le service de génération est momentanément indisponible. Réessayez dans quelques instants.";
  }
  if (status === 404) return "Ce projet est introuvable.";
  return data?.detail || "Une erreur inattendue est survenue.";
}

async function requete(chemin, options = {}) {
  let reponse;
  try {
    reponse = await fetch(`/api${chemin}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error("Impossible de joindre le serveur. Vérifiez que l'application est démarrée.");
  }
  const data = await reponse.json().catch(() => null);
  if (!reponse.ok) throw new Error(messageErreur(reponse.status, data));
  return data;
}

export const api = {
  creerProjet: (description) =>
    requete("/projects", { method: "POST", body: JSON.stringify(description) }),
  listerProjets: () => requete("/projects"),
  obtenirProjet: (id) => requete(`/projects/${id}`),
};
