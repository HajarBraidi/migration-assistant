// Description du formulaire : un seul endroit à modifier pour ajouter un champ.
// Les valeurs correspondent exactement au contrat (schemas.py).

export const SECTIONS = [
  {
    id: "general",
    titre: "Informations générales",
    description: "L'application à migrer et la raison de la migration.",
    champs: [
      { name: "nom", label: "Nom de l'application", type: "text", required: true, placeholder: "Ex. StockPro" },
      {
        name: "domaine", label: "Domaine", type: "select", required: true,
        options: ["Gestion de stock", "E-commerce", "RH", "Finance", "Autre"],
      },
      {
        name: "objectifs", label: "Objectifs de la migration", type: "multi", required: true, full: true,
        options: ["Réduire les coûts", "Performances", "Moderniser", "Sécuriser", "Scalabilité"],
      },
      {
        name: "problemes_actuels", label: "Problèmes actuels", type: "multi", full: true,
        options: ["Lenteur", "Pannes", "Bugs", "Failles de sécurité", "Code difficile à maintenir"],
      },
    ],
  },
  {
    id: "technologies",
    titre: "Technologies actuelles",
    description: "Le langage, le framework et l'interface utilisés aujourd'hui.",
    champs: [
      {
        name: "langage", label: "Langage", type: "select", required: true,
        options: ["PHP", "Java", "Python", "C#", "JavaScript", "Autre"],
      },
      { name: "version_langage", label: "Version du langage", type: "text", placeholder: "Ex. 5.6" },
      { name: "framework_backend", label: "Framework back-end", type: "text", placeholder: "Ex. Laravel, Spring, aucun" },
      {
        name: "interface_utilisateur", label: "Interface utilisateur", type: "select", required: true,
        options: ["HTML/jQuery", "AngularJS", "Angular", "React", "Vue", "Autre"],
      },
    ],
  },
  {
    id: "donnees",
    titre: "Base de données",
    description: "Le système de stockage et le volume des données.",
    champs: [
      {
        name: "type_base_donnees", label: "Type de base", type: "select", required: true,
        options: ["MySQL", "PostgreSQL", "Oracle", "SQL Server", "MongoDB", "Autre"],
      },
      {
        name: "volume_donnees", label: "Volume des données", type: "select", required: true,
        options: ["< 10 Go", "10 à 100 Go", "100 Go à 1 To", "> 1 To"],
      },
    ],
  },
  {
    id: "architecture",
    titre: "Architecture et hébergement",
    description: "L'organisation de l'application et son hébergement.",
    champs: [
      {
        name: "type_architecture", label: "Architecture", type: "select", required: true,
        options: ["Monolithe", "Plusieurs services", "Je ne sais pas"],
      },
      {
        name: "hebergement_actuel", label: "Hébergement actuel", type: "select", required: true,
        options: ["Serveur local", "Hébergeur", "Cloud"],
      },
      {
        name: "hebergement_cible", label: "Hébergement cible souhaité", type: "select",
        options: ["Pas de préférence", "AWS", "Azure", "GCP", "Local"],
      },
      { name: "integrations_externes", label: "Intégrations externes", type: "text", placeholder: "Ex. API de paiement, ERP" },
    ],
  },
  {
    id: "utilisation",
    titre: "Utilisation",
    description: "Le nombre d'utilisateurs et son évolution.",
    champs: [
      {
        name: "nombre_utilisateurs", label: "Nombre d'utilisateurs", type: "select", required: true,
        options: ["< 100", "100 à 1 000", "1 000 à 50 000", "> 50 000"],
      },
      {
        name: "evolution_prevue", label: "Évolution prévue", type: "select", required: true,
        options: ["Stable", "Croissance modérée", "Croissance forte"],
      },
    ],
  },
  {
    id: "contraintes",
    titre: "Contraintes",
    description: "Elles déterminent la stratégie recommandée.",
    champs: [
      { name: "budget", label: "Budget", type: "select", required: true, options: ["Faible", "Moyen", "Élevé"] },
      {
        name: "delai", label: "Délai souhaité", type: "select", required: true,
        options: ["< 3 mois", "3 à 6 mois", "6 à 12 mois", "> 12 mois"],
      },
      {
        name: "interruption_acceptable", label: "Interruption de service acceptable", type: "select", required: true,
        options: ["Aucune", "Quelques heures", "Quelques jours"],
      },
      { name: "taille_equipe", label: "Taille de l'équipe", type: "number", required: true, placeholder: "Ex. 3" },
      {
        name: "exigences_securite", label: "Exigences de sécurité et légales", type: "multi", full: true,
        options: ["Données personnelles (RGPD / loi 09-08)", "Données bancaires", "Données de santé"],
      },
      { name: "competences_equipe", label: "Compétences de l'équipe", type: "text", full: true, placeholder: "Ex. PHP, MySQL, notions de Linux" },
    ],
  },
  {
    id: "details",
    titre: "Détails complémentaires",
    description: "Toute information utile pour affiner le plan.",
    champs: [
      {
        name: "description_libre", label: "Description libre", type: "textarea", full: true,
        placeholder: "Contexte, contraintes particulières, fonctionnalités critiques…",
      },
    ],
  },
];

export const VALEURS_INITIALES = Object.fromEntries(
  SECTIONS.flatMap((s) => s.champs).map((c) => [c.name, c.type === "multi" ? [] : ""])
);
VALEURS_INITIALES.hebergement_cible = "Pas de préférence";

export const EXEMPLE_STOCKPRO = {
  nom: "StockPro",
  domaine: "Gestion de stock",
  objectifs: ["Réduire les coûts", "Moderniser"],
  problemes_actuels: ["Lenteur", "Pannes"],
  langage: "PHP",
  version_langage: "5.6",
  framework_backend: "Aucun",
  interface_utilisateur: "HTML/jQuery",
  type_base_donnees: "MySQL",
  volume_donnees: "< 10 Go",
  type_architecture: "Monolithe",
  hebergement_actuel: "Serveur local",
  hebergement_cible: "Pas de préférence",
  integrations_externes: "",
  nombre_utilisateurs: "100 à 1 000",
  evolution_prevue: "Stable",
  budget: "Faible",
  delai: "< 3 mois",
  interruption_acceptable: "Quelques heures",
  exigences_securite: ["Données personnelles (RGPD / loi 09-08)"],
  taille_equipe: "2",
  competences_equipe: "PHP, MySQL, notions de Linux",
  description_libre: "Application interne utilisée par 200 employés.",
};

// Transforme les valeurs du formulaire au format attendu par l'API
export function versDescription(valeurs) {
  const description = {};
  for (const [cle, valeur] of Object.entries(valeurs)) {
    description[cle] = typeof valeur === "string" && valeur.trim() === "" ? null : valeur;
  }
  description.taille_equipe = Number(valeurs.taille_equipe);
  return description;
}

// Vérifie les champs obligatoires avant l'envoi
export function valider(valeurs) {
  const erreurs = {};
  for (const champ of SECTIONS.flatMap((s) => s.champs)) {
    if (!champ.required) continue;
    const v = valeurs[champ.name];
    if (champ.type === "multi" ? v.length === 0 : String(v).trim() === "") {
      erreurs[champ.name] = "Ce champ est obligatoire.";
    }
  }
  const taille = Number(valeurs.taille_equipe);
  if (valeurs.taille_equipe !== "" && (!Number.isInteger(taille) || taille < 1 || taille > 500)) {
    erreurs.taille_equipe = "Indiquez un nombre entre 1 et 500.";
  }
  return erreurs;
}

export const STRATEGIES = {
  Retire: "Retirer l'application qui n'est plus utile.",
  Retain: "Conserver l'application en l'état pour le moment.",
  Rehost: "Déplacer l'application telle quelle, sans modifier le code.",
  Relocate: "Déplacer l'environnement complet sans le modifier.",
  Replatform: "Déplacer l'application avec des adaptations ciblées.",
  Repurchase: "Remplacer l'application par une solution du marché.",
  Refactor: "Réécrire ou réorganiser profondément l'application.",
};
