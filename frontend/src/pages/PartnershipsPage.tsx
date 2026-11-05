import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { useCurrentUser } from "../features/auth/hooks";
import { getOrganizations } from "../features/organizations/api";
import { confirmPartnership, createOpportunity, getOpportunities, getPartnerships, respondToOpportunity, updateResponse } from "../features/partnerships/api";
import "./CabinetPages.css";

type Tab = "market" | "mine" | "incoming" | "active" | "create";

export function PartnershipsPage() {
  const [tab, setTab] = useState<Tab>("market");
  const qc = useQueryClient();
  const user = useCurrentUser();
  const institution = user.data?.organization?.type === "institution";
  const opportunities = useQuery({ queryKey: ["opportunities", tab], queryFn: () => getOpportunities(tab === "mine" ? "mine" : tab === "incoming" ? "incoming" : ""), enabled: tab !== "active" && tab !== "create" });
  const partnerships = useQuery({ queryKey: ["partnerships"], queryFn: getPartnerships });
  const organizations = useQuery({ queryKey: ["organizations", "partnership-targets"], queryFn: () => getOrganizations() });
  const refresh = () => { void qc.invalidateQueries({ queryKey: ["opportunities"] }); void qc.invalidateQueries({ queryKey: ["partnerships"] }); void qc.invalidateQueries({ queryKey: ["organization"] }); };
  const respond = useMutation({ mutationFn: (id: string) => respondToOpportunity(id, "Готовы обсудить программу, вклад сторон и сроки реализации."), onSuccess: refresh });
  const status = useMutation({ mutationFn: ({ id, value }: { id: string; value: "accepted" | "rejected" }) => updateResponse(id, value), onSuccess: refresh });
  const confirm = useMutation({ mutationFn: confirmPartnership, onSuccess: refresh });
  const create = useMutation({ mutationFn: createOpportunity, onSuccess: () => { refresh(); setTab("mine"); } });
  const targets = organizations.data?.filter(item => item.id !== user.data?.organization_id && (institution ? item.type !== "institution" : item.type === "institution"));

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    create.mutate({ direction: institution ? "institution_seeks_organization" : "organization_seeks_institution", target_organization_id: form.get("target_organization_id") || null, title: String(form.get("title")), description: String(form.get("description")), topic: String(form.get("topic")), format: String(form.get("format")), target_audience: String(form.get("target_audience")), conditions: String(form.get("conditions")), desired_start: form.get("desired_start") || null, desired_end: form.get("desired_end") || null });
  }

  return <AppShell><section className="page-section"><div className="page-shell"><div className="cabinet-head"><div><span className="chip">Совместные инициативы</span><h1 className="page-heading">Партнёрства</h1></div><button className="button button-primary" onClick={() => setTab("create")}>Создать запрос</button></div><nav className="cabinet-tabs">{([["market", "Открытые"], ["mine", "Исходящие"], ["incoming", "Входящие"], ["active", "Партнёрства"]] as [Tab, string][]).map(([id, label]) => <button className={tab === id ? "active" : ""} onClick={() => setTab(id)} key={id}>{label}</button>)}</nav>
    {tab === "create" ? <form className="surface panel form-grid" onSubmit={submit}><h2 className="wide">Новая возможность</h2><div className="field wide"><label>Название</label><input name="title" required minLength={3} /></div><div className="field wide"><label>Описание</label><textarea name="description" required minLength={20} /></div><div className="field"><label>Тема</label><input name="topic" required /></div><div className="field"><label>Формат</label><input name="format" defaultValue="Очно и онлайн" required /></div><div className="field wide"><label>Адресат</label><select name="target_organization_id"><option value="">Публичный запрос</option>{targets?.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></div><div className="field wide"><label>Целевая аудитория</label><input name="target_audience" defaultValue="Учащиеся 8–11 классов" required /></div><div className="field wide"><label>Условия</label><textarea name="conditions" /></div><div className="field"><label>Начало</label><input name="desired_start" type="date" /></div><div className="field"><label>Окончание</label><input name="desired_end" type="date" /></div><button className="button button-primary">Опубликовать</button></form>
    : tab === "active" ? <div className="opportunity-grid">{partnerships.data?.map(item => <article className="surface opportunity-card" key={item.id}><span className={`status status--${item.status}`}>{item.status}</span><h3>{item.title}</h3><p>{item.organization_a.name} × {item.organization_b.name}</p><div className="partnership-progress"><span className={item.organization_a_confirmed ? "done" : ""}>{item.organization_a_confirmed ? "✓ " : ""}{item.organization_a.name}</span><span className={item.organization_b_confirmed ? "done" : ""}>{item.organization_b_confirmed ? "✓ " : ""}{item.organization_b.name}</span></div>{item.status === "active" && <button className="button button-primary" onClick={() => confirm.mutate(item.id)}>Подтвердить завершение</button>}</article>)}</div>
    : <div className="opportunity-grid">{opportunities.data?.map(item => <article className="surface opportunity-card" key={item.id}><div className="org-meta"><span className="chip">{item.topic}</span><span>◆ {item.creator.prestige_score}</span></div><h3>{item.title}</h3><p>{item.description}</p><small>{item.creator.name} · {item.target ? `для ${item.target.name}` : "публично"} · {item.format}</small>{tab === "market" && item.creator.id !== user.data?.organization_id && <div className="row-actions opportunity-actions"><button className="button button-primary" onClick={() => respond.mutate(item.id)}>Откликнуться</button></div>}{(tab === "mine" || tab === "incoming") && item.responses.map(response => <div className="response-row" key={response.id}><div><strong>{response.responder.name}</strong><p>{response.message}</p></div>{tab === "mine" && response.status === "pending" && <div className="row-actions"><button className="button button-primary" onClick={() => status.mutate({ id: response.id, value: "accepted" })}>Принять</button><button className="button button-ghost" onClick={() => status.mutate({ id: response.id, value: "rejected" })}>Отклонить</button></div>}</div>)}</article>)}</div>}
  </div></section></AppShell>;
}
