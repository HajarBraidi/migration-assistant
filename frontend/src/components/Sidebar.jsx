import { FilePlus2, History, LogOut } from "lucide-react";
import Logo from "./Logo.jsx";

const LIENS = [
  { id: "form", libelle: "Nouvelle analyse", icone: FilePlus2 },
  { id: "history", libelle: "Historique", icone: History },
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
