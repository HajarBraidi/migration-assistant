import { Calculator, FilePlus2, FolderKanban, LogOut, ScanSearch } from "lucide-react";
import Logo from "./Logo.jsx";

// Le menu est organisé par groupes : ajouter une entrée = ajouter une ligne ici
const GROUPES = [
  {
    titre: "Principal",
    liens: [
      { id: "form", libelle: "Nouvelle analyse", icone: FilePlus2 },
      { id: "history", libelle: "Mes projets", icone: FolderKanban },
    ],
  },
  {
    titre: "Outils",
    liens: [
      { id: "scanner", libelle: "Scanner de code", icone: ScanSearch },
      { id: "couts", libelle: "Comparateur de coûts", icone: Calculator },
    ],
  },
];

const initiales = (nom) =>
  nom.split(" ").filter(Boolean).slice(0, 2).map((m) => m[0].toUpperCase()).join("");

export default function Sidebar({ vue, onNaviguer, utilisateur, onDeconnecter }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <Logo />
        <div>
          <div className="brand-name">MigraPlan</div>
          <div className="brand-tagline">Assistant de migration</div>
        </div>
      </div>

      <nav className="nav">
        {GROUPES.map((groupe) => (
          <div key={groupe.titre} className="nav-group">
            <div className="nav-group-title">{groupe.titre}</div>
            {groupe.liens.map(({ id, libelle, icone: Icone }) => (
              <button
                key={id}
                className={`nav-link ${vue === id ? "active" : ""}`}
                onClick={() => onNaviguer(id)}
                aria-label={libelle}
              >
                <Icone size={18} />
                <span className="nav-label">{libelle}</span>
              </button>
            ))}
          </div>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <div className="user">
          <span className="avatar">{initiales(utilisateur.nom)}</span>
          <div className="user-info">
            <div className="user-name">{utilisateur.nom}</div>
            <div className="user-email">{utilisateur.email}</div>
          </div>
          <button className="icon-btn" onClick={onDeconnecter} aria-label="Se déconnecter" title="Se déconnecter">
            <LogOut size={18} />
          </button>
        </div>
        <div className="sidebar-footer">
          Plans générés par IA générative. À valider par un architecte avant mise en œuvre.
        </div>
      </div>
    </aside>
  );
}
