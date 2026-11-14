import { useEffect, useId, useState } from "react";

// Couleur de chaque type de composant (cohérente avec la charte de l'application)
const STYLES = {
  utilisateur: "fill:#f1f5f9,stroke:#64748b,color:#0f172a",
  frontend: "fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e",
  backend: "fill:#eef2ff,stroke:#4f46e5,color:#312e81",
  base_de_donnees: "fill:#dcfce7,stroke:#16a34a,color:#14532d",
  service_externe: "fill:#fef3c7,stroke:#d97706,color:#78350f",
  infrastructure: "fill:#f5f3ff,stroke:#7c3aed,color:#4c1d95",
};

// Forme de chaque type : base de données en cylindre, utilisateur arrondi, etc.
const FORMES = {
  utilisateur: (t) => `(["${t}"])`,
  base_de_donnees: (t) => `[("${t}")]`,
  service_externe: (t) => `{{"${t}"}}`,
};

const nettoyer = (texte) => String(texte).replace(/["<>]/g, "'");

// Transforme le schéma (composants + liens) en code Mermaid
export function versMermaid(diagramme) {
  const lignes = ["flowchart LR"];
  for (const c of diagramme.composants) {
    const forme = FORMES[c.type] || ((t) => `["${t}"]`);
    lignes.push(`  ${c.id}${forme(nettoyer(c.libelle))}:::${c.type}`);
  }
  for (const l of diagramme.liens) {
    lignes.push(l.libelle ? `  ${l.source} -->|"${nettoyer(l.libelle)}"| ${l.cible}` : `  ${l.source} --> ${l.cible}`);
  }
  for (const [type, style] of Object.entries(STYLES)) {
    lignes.push(`  classDef ${type} ${style}`);
  }
  return lignes.join("\n");
}

export default function ArchitectureDiagram({ titre, diagramme }) {
  const id = `schema-${useId().replace(/:/g, "")}`;
  const [svg, setSvg] = useState("");
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    let actif = true;
    // Mermaid est chargé seulement quand un schéma est affiché (page plus légère)
    import("mermaid")
      .then(({ default: mermaid }) => {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          fontFamily: "Inter, system-ui, sans-serif",
          themeVariables: { lineColor: "#94a3b8", fontSize: "14px", edgeLabelBackground: "#ffffff" },
        });
        return mermaid.render(id, versMermaid(diagramme));
      })
      .then((resultat) => actif && setSvg(resultat.svg))
      .catch(() => actif && setErreur(true));
    return () => {
      actif = false;
    };
  }, [id, diagramme]);

  return (
    <figure className="diagram">
      <figcaption>{titre}</figcaption>
      {erreur ? (
        <p className="muted">Le schéma n'a pas pu être affiché.</p>
      ) : (
        <div className="diagram-canvas" dangerouslySetInnerHTML={{ __html: svg }} />
      )}
    </figure>
  );
}
