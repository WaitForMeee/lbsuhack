import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { getOrganizations } from "../features/organizations/api";
import "./PublicPages.css";

const labels = { institution: "Учреждение", company: "Компания", academy: "Академия" };

export function OrganizationsPage() {
  const [search, setSearch] = useState("");
  const organizations = useQuery({ queryKey: ["organizations", search], queryFn: () => getOrganizations(search ? `search=${encodeURIComponent(search)}` : "") });
  return <AppShell><section className="page-section"><div className="page-shell"><div className="toolbar"><div><span className="chip">Партнёры</span><h1 className="page-heading">Организации</h1></div><input className="input org-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Поиск по названию и направлениям" /></div><div className="org-grid">{organizations.data?.map(org => <a className="org-card surface" href={`/organizations/${org.id}`} key={org.id}><div className="org-meta"><span className="chip">{labels[org.type]}</span><span>{org.region}</span></div><h3>{org.name}</h3><p className="muted">{org.description}</p><div className="org-meta"><span className="prestige">◆ {org.prestige_score} престиж</span><span>· {org.published_event_count} событий</span></div></a>)}</div></div></section></AppShell>;
}
