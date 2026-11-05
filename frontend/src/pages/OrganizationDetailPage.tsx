import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { getEvents } from "../features/events/api";
import { EventCard } from "../features/events/components/EventCard";
import { getOrganization } from "../features/organizations/api";
import "./PublicPages.css";

export function OrganizationDetailPage() {
  const { id = "" } = useParams();
  const org = useQuery({ queryKey: ["organization", id], queryFn: () => getOrganization(id) });
  const events = useQuery({ queryKey: ["events", "org", id], queryFn: () => getEvents(`organizer_id=${id}&include_past=true`) });
  if (!org.data) return <AppShell><section className="page-section"><div className="page-shell skeleton" /></section></AppShell>;
  return <AppShell><section className="page-section"><div className="page-shell"><span className="chip">{org.data.type}</span><h1 className="page-heading org-detail-title">{org.data.name}</h1><p className="muted org-detail-description">{org.data.description}</p><div className="surface prestige-panel"><strong className="prestige">◆ {org.data.prestige_score} престиж</strong><p className="muted">Престиж начисляется только за совместные инициативы, завершение которых подтвердили обе стороны.</p><div className="stack">{org.data.prestige_history.map(entry => <div key={entry.id}><strong>+{entry.points}</strong> · {entry.reason}</div>)}</div></div><div className="section-head"><h2 className="section-heading">События организации</h2></div><div className="card-grid">{events.data?.items.map(event => <EventCard key={event.id} event={event} />)}</div></div></section></AppShell>;
}
