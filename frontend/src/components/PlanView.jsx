import {
  AlertTriangle,
  ArrowLeft,
  Eye,
  History,
  CalendarClock,
  ClipboardList,
  Download,
  Layers,
  RotateCcw,
  Shuffle,
  ShieldAlert,
  Target,
  Users,
  Wallet,
  Cloud,
  Rocket,
} from "lucide-react";
import { STRATEGIES } from "../formConfig.js";
import ArchitectureDiagram from "./ArchitectureDiagram.jsx";
import AssistantChat from "./AssistantChat.jsx";
import VersionsPanel from "./VersionsPanel.jsx";
import CostComparison from "./CostComparison.jsx";
import DeploymentKit from "./DeploymentKit.jsx";
import { api } from "../api.js";
import { useState } from "react";

const formatDate = (iso) =>
  new Date(iso).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" });

function Section({ icone: Icone, titre, children }) {
  return (
    <section className="card plan-section">
      <h2 className="section-title">
        <Icone size={18} />
        {titre}
      </h2>
      {children}
    </section>
  );
}

function Niveau({ niveau }) {
  const classe = { Faible: "low", Moyen: "medium", Élevé: "high" }[niveau] || "medium";
  return <span className={`badge badge-${classe}`}>{niveau}</span>;
}

function Indicateur({ icone: Icone, libelle, valeur }) {
  return (
    <div className="kpi">
      <Icone size={18} />
      <div>
        <div className="kpi-label">{libelle}</div>
        <div className="kpi-value">{valeur}</div>
      </div>
    </div>
  );
}

export default function PlanView({ projet, onRetour, onMiseAJour }) {
  // Version consultée : null = la version actuelle
  const [ancienne, setAncienne] = useState(null);
  const [erreurVersion, setErreurVersion] = useState(null);
  const derniere = projet.versions.length;
  const { plan, avertissements } = ancienne || projet;
  const version = ancienne ? ancienne.numero : derniere;

  const voirVersion = async (numero) => {
    setErreurVersion(null);
    try {
      setAncienne(numero === derniere ? null : await api.obtenirVersion(projet.id, numero));
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setErreurVersion(e.message);
    }
  };

  const restaurer = async () => {
    setErreurVersion(null);
    try {
      onMiseAJour(await api.restaurerVersion(projet.id, ancienne.numero));
      setAncienne(null);
    } catch (e) {
      setErreurVersion(e.message);
    }
  };

  return (
    <div className="page page-plan">
      <div className="plan-layout">
        <div className="plan-main">
          <div className="toolbar no-print">
            <button className="btn btn-ghost" onClick={onRetour}>
              <ArrowLeft size={16} />
              Retour
            </button>
            <button className="btn btn-secondary" onClick={() => window.print()}>
              <Download size={16} />
              Exporter en PDF
            </button>
          </div>

          <header className="plan-hero card">
            <div>
              <p className="eyebrow">Plan de migration</p>
              <h1>{projet.nom}</h1>
              <p className="subtitle">
                Généré le {formatDate(projet.cree_le)}
                <span className="badge badge-neutral version-badge">
                  Version {version}
                  {version === derniere ? " (actuelle)" : ""}
                </span>
              </p>
            </div>
            <div className="strategy-pill">
              <span className="strategy-label">Stratégie recommandée</span>
              <span className="strategy-name">{plan.strategie.strategie}</span>
              <span className="strategy-desc">{STRATEGIES[plan.strategie.strategie]}</span>
            </div>
          </header>

          {ancienne && (
            <div className="alert alert-info no-print">
              <Eye size={18} />
              <div className="alert-body">
                <span>
                  Vous consultez la <strong>version {ancienne.numero}</strong> ({ancienne.origine}).
                  La version actuelle est la V{derniere}.
                </span>
                <div className="alert-actions">
                  <button className="btn btn-primary btn-sm" onClick={restaurer}>
                    <History size={14} />
                    Restaurer cette version
                  </button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setAncienne(null)}>
                    Revenir à la version actuelle
                  </button>
                </div>
              </div>
            </div>
          )}
          {erreurVersion && (
            <div className="alert alert-error">
              <AlertTriangle size={18} />
              <span>{erreurVersion}</span>
            </div>
          )}

          <div className="kpis">
            <Indicateur
              icone={CalendarClock}
              libelle="Durée totale"
              valeur={`${plan.estimation.duree_totale_semaines} semaines`}
            />
            <Indicateur icone={Layers} libelle="Phases" valeur={plan.phases.length} />
            <Indicateur icone={Shuffle} libelle="Bascule" valeur={plan.bascule.type} />
            <Indicateur
              icone={ShieldAlert}
              libelle="Risques identifiés"
              valeur={plan.risques.length}
            />
          </div>

          {avertissements.length > 0 && (
            <div className="alert alert-warning">
              <AlertTriangle size={18} />
              <div>
                <strong>Points de vigilance détectés par les règles de cohérence</strong>
                <ul>
                  {avertissements.map((a) => (
                    <li key={a}>{a}</li>
                  ))}
                </ul>
              </div>
            </div>
          )}

          {derniere > 1 && (
            <VersionsPanel
              versions={projet.versions}
              numeroAffiche={version}
              onVoir={voirVersion}
            />
          )}

          <Section icone={ClipboardList} titre="1. Résumé de l'existant">
            <p>{plan.resume_existant.resume}</p>
            <h3>Points faibles</h3>
            <ul className="list">
              {plan.resume_existant.points_faibles.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          </Section>

          <Section icone={Target} titre="2. Stratégie recommandée">
            <p>
              <strong>{plan.strategie.strategie}</strong> — {plan.strategie.justification}
            </p>
          </Section>

          <Section icone={Layers} titre="3. Architecture cible">
            {plan.schema_avant && plan.schema_apres && (
              <div className="diagrams">
                <ArchitectureDiagram titre="Architecture actuelle" diagramme={plan.schema_avant} />
                <ArchitectureDiagram titre="Architecture cible" diagramme={plan.schema_apres} />
              </div>
            )}
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Composant</th>
                    <th>Choix</th>
                    <th>Justification</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.architecture_cible.map((c) => (
                    <tr key={c.composant}>
                      <td className="strong">{c.composant}</td>
                      <td>{c.choix}</td>
                      <td>{c.justification}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section icone={CalendarClock} titre="4. Phases de migration">
            <ol className="timeline">
              {plan.phases.map((phase, i) => (
                <li key={phase.nom}>
                  <span className="timeline-dot">{i + 1}</span>
                  <div className="timeline-body">
                    <div className="timeline-head">
                      <h3>{phase.nom}</h3>
                      <span className="badge badge-neutral">{phase.duree_semaines} sem.</span>
                    </div>
                    <p>{phase.description}</p>
                    <ul className="list">
                      {phase.taches.map((t) => (
                        <li key={t}>{t}</li>
                      ))}
                    </ul>
                  </div>
                </li>
              ))}
            </ol>
          </Section>

          <Section icone={Shuffle} titre="5. Stratégie de bascule">
            <p>
              <strong>{plan.bascule.type}</strong> — {plan.bascule.justification}
            </p>
            <ol className="list numbered">
              {plan.bascule.deroulement.map((d) => (
                <li key={d}>{d}</li>
              ))}
            </ol>
          </Section>

          <Section icone={ShieldAlert} titre="6. Risques et solutions">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Risque</th>
                    <th>Niveau</th>
                    <th>Solution prévue</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.risques.map((r) => (
                    <tr key={r.risque}>
                      <td>{r.risque}</td>
                      <td>
                        <Niveau niveau={r.niveau} />
                      </td>
                      <td>{r.solution}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section icone={RotateCcw} titre="7. Plan de rollback">
            <p>
              <strong>Déclencheur :</strong> {plan.rollback.declencheur}
            </p>
            <ol className="list numbered">
              {plan.rollback.etapes.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ol>
          </Section>

          <Section icone={Wallet} titre="8. Estimation">
            <div className="estimate">
              <div>
                <span className="kpi-label">Durée totale</span>
                <strong>{plan.estimation.duree_totale_semaines} semaines</strong>
              </div>
              <div>
                <span className="kpi-label">Ordre de coût</span>
                <strong>{plan.estimation.cout}</strong>
              </div>
            </div>
            <h3>
              <Users size={16} /> Équipe
            </h3>
            <ul className="list">
              {plan.estimation.equipe.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </Section>

          {projet.description && (
            <Section icone={Cloud} titre="Coût d'hébergement cloud estimé">
              <CostComparison
                demande={{
                  nombre_utilisateurs: projet.description.nombre_utilisateurs,
                  volume_donnees: projet.description.volume_donnees,
                  type_base_donnees: projet.description.type_base_donnees,
                  haute_disponibilite: projet.description.interruption_acceptable === "Aucune",
                }}
                cible={projet.description.hebergement_cible}
              />
            </Section>
          )}

          {projet.description && (
            <div className="no-print">
              <Section icone={Rocket} titre="Kit de déploiement">
                <DeploymentKit description={projet.description} />
              </Section>
            </div>
          )}
        </div>

        <aside className="plan-chat no-print">
          <AssistantChat
            projet={projet}
            onMiseAJour={onMiseAJour}
            lectureSeule={Boolean(ancienne)}
          />
        </aside>
      </div>
    </div>
  );
}
