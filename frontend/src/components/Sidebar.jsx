import { FilePlus2, History } from "lucide-react";
import Logo from "./Logo.jsx";

const LIENS = [
  { id: "form", libelle: "Nouvelle analyse", icone: FilePlus2 },
  { id: "history", libelle: "Historique", icone: History },
];

export default function Sidebar({ vue, onNaviguer }) {
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
        {LIENS.map(({ id, libelle, icone: Icone }) => (
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
      </nav>

      <div className="sidebar-footer">
        Plans générés par IA générative. À valider par un architecte avant mise en œuvre.
      </div>
    </aside>
  );
}
