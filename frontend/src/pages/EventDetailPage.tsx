import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { ContentState } from "../components/feedback/ContentState";
import { AppShell } from "../components/layout/AppShell";
import { useCurrentUser } from "../features/auth/hooks";
import { getEvent, registerForEvent } from "../features/events/api";
import { formatDate } from "../features/events/components/EventCard";
import "./PublicPages.css";

export function EventDetailPage() {
  const { slug = "" } = useParams();
  const client = useQueryClient();
  const user = useCurrentUser();
  const event = useQuery({ queryKey: ["event", slug], queryFn: () => getEvent(slug) });
  const register = useMutation({ mutationFn: registerForEvent, onSuccess: () => client.invalidateQueries({ queryKey: ["event", slug] }) });
  if (event.isPending) return <AppShell><section className="page-section"><div className="page-shell skeleton" /></section></AppShell>;
  if (!event.data) return <AppShell><section className="page-section"><div className="page-shell"><ContentState title="Событие не найдено" /></div></section></AppShell>;
  const item = event.data;
  const canRegister = user.data?.role === "student" && !item.my_registration_status;
  return <AppShell><section className="page-section"><div className="page-shell"><div className="chip-row">{item.categories.map(category => <span className="chip" key={category.id}>{category.name}</span>)}</div><h1 className="page-heading event-detail-title">{item.title}</h1><img className="event-detail-cover" src={item.image_url ?? "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1400&q=80"} alt="" /><div className="event-detail-grid"><article className="event-detail-copy"><h2 className="section-heading">О событии</h2><p>{item.description}</p><h2 className="section-heading">Условия участия</h2><p>{item.participation_terms || "Специальных условий нет."}</p></article><aside><div className="surface fact-card"><div className="fact-list"><div><span>Дата и время</span><strong>{formatDate(item.starts_at)}</strong></div><div><span>Формат</span><strong>{item.format === "offline" ? "Офлайн" : item.format === "online" ? "Онлайн" : "Гибрид"}</strong></div><div><span>Место</span><strong>{item.venue ?? item.meeting_url ?? "Будет сообщено"}</strong></div><div><span>Для кого</span><strong>{item.target_audience}</strong></div><div><span>Организатор</span><strong>{item.organizer.name}</strong></div></div>{item.my_registration_status ? <span className={`status status--${item.my_registration_status}`}>Заявка: {item.my_registration_status}</span> : canRegister ? <button className="button button-primary full-button" disabled={register.isPending} onClick={() => register.mutate(item.id)}>Зарегистрироваться</button> : <a className="button button-primary full-button" href={user.data ? "/student" : "/login"}>{user.data ? "Доступно учащимся" : "Войти и зарегистрироваться"}</a>}{register.error && <p className="error-message">{register.error.message}</p>}</div></aside></div></div></section></AppShell>;
}
