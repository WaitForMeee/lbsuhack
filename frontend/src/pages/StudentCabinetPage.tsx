import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ContentState } from "../components/feedback/ContentState";
import { LoadingState } from "../components/feedback/LoadingState";
import { AppShell } from "../components/layout/AppShell";
import { cancelRegistration, getCategories, getMyRegistrations, getRecommendations } from "../features/events/api";
import { EventCard } from "../features/events/components/EventCard";
import { RegistrationCard } from "../features/events/components/RegistrationCard";
import { AchievementCard } from "../features/profiles/AchievementCard";
import { getPortfolio, getProfile, updateInterests, updateProfile, type StudentProfile } from "../features/profiles/api";
import "./CabinetPages.css";

type Tab = "recommendations" | "registrations" | "portfolio" | "profile";

export function StudentCabinetPage() {
  const [tab, setTab] = useState<Tab>("recommendations");
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ["profile"], queryFn: getProfile, enabled: tab === "profile" });
  const categories = useQuery({ queryKey: ["categories"], queryFn: getCategories, enabled: tab === "profile" });
  const recommendations = useQuery({ queryKey: ["recommendations"], queryFn: getRecommendations, enabled: tab === "recommendations" });
  const registrations = useQuery({ queryKey: ["registrations", "me"], queryFn: getMyRegistrations, enabled: tab === "registrations" });
  const portfolio = useQuery({ queryKey: ["portfolio"], queryFn: getPortfolio, enabled: tab === "portfolio" });
  const interests = useMutation({
    mutationKey: ["profile-interests"],
    mutationFn: updateInterests,
    scope: { id: "profile-interests" },
    onMutate: async categoryIds => {
      await queryClient.cancelQueries({ queryKey: ["profile"] });
      const previous = queryClient.getQueryData<StudentProfile>(["profile"]);
      queryClient.setQueryData<StudentProfile>(["profile"], current => current ? {
        ...current,
        interests: (categories.data ?? []).filter(category => categoryIds.includes(category.id)),
      } : current);
      return { previous };
    },
    onError: (_error, _categoryIds, context) => queryClient.setQueryData(["profile"], context?.previous),
    onSettled: async () => {
      if (queryClient.isMutating({ mutationKey: ["profile-interests"] }) !== 1) return;
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["profile"] }),
        queryClient.invalidateQueries({ queryKey: ["recommendations"] }),
      ]);
    },
  });
  const cancel = useMutation({ mutationFn: cancelRegistration, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["registrations"] }) });
  const saveProfile = useMutation({ mutationFn: updateProfile, onSuccess: () => queryClient.invalidateQueries({ queryKey: ["profile"] }) });
  const selected = new Set(profile.data?.interests.map(item => item.id));
  const upcoming = registrations.data?.filter(item => ["pending", "approved"].includes(item.status) && new Date(item.event_starts_at) >= new Date()) ?? [];
  const completed = registrations.data?.filter(item => !upcoming.some(active => active.id === item.id)) ?? [];

  function toggleInterest(id: string) {
    const current = queryClient.getQueryData<StudentProfile>(["profile"]);
    const currentIds = current?.interests.map(item => item.id) ?? [];
    interests.mutate(currentIds.includes(id) ? currentIds.filter(item => item !== id) : [...currentIds, id]);
  }

  return <AppShell><section className="page-section"><div className="page-shell">
    <div className="cabinet-head"><div><span className="chip">Кабинет учащегося</span><h1 className="page-heading">Мои возможности</h1></div></div>
    <nav className="cabinet-tabs" aria-label="Разделы кабинета">{([["recommendations", "Рекомендации"], ["registrations", "Мои заявки"], ["portfolio", "Портфолио"], ["profile", "Профиль"]] as [Tab, string][]).map(([id, label]) => <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)} type="button">{label}</button>)}</nav>

    {tab === "recommendations" ? <div><div className="section-head"><h2 className="section-heading">Подобрано по интересам</h2></div>{recommendations.isPending ? <LoadingState label="Подбираем события" /> : recommendations.data?.items.length ? <div className="card-grid">{recommendations.data.items.slice(0, 9).map(event => <EventCard event={event} key={event.id} />)}</div> : <ContentState title="Пока нет рекомендаций" description="Выберите интересы или откройте полный каталог событий." action={<a className="button button-primary" href="/events">Открыть каталог</a>} />}</div> : null}

    {tab === "registrations" ? registrations.isPending ? <LoadingState label="Загружаем заявки" /> : <div className="registration-sections"><section className="registration-section"><div className="registration-section__heading"><h2>Предстоящие</h2><span>{upcoming.length}</span></div>{upcoming.length ? upcoming.map(item => <RegistrationCard key={item.id} registration={item} isCancelling={cancel.isPending && cancel.variables === item.id} onCancel={() => cancel.mutate(item.id)} />) : <ContentState title="Нет предстоящих событий" description="Найдите событие и отправьте заявку на участие." action={<a className="button button-primary" href="/events">Найти событие</a>} />}</section><section className="registration-section"><div className="registration-section__heading"><h2>Завершённые</h2><span>{completed.length}</span></div>{completed.length ? completed.map(item => <RegistrationCard key={item.id} registration={item} />) : <ContentState title="История пока пуста" description="Здесь появятся завершённые, отменённые и отклонённые заявки." />}</section></div> : null}

    {tab === "portfolio" ? <div><div className="section-head"><h2 className="section-heading">Подтверждённые участия</h2></div>{portfolio.isPending ? <LoadingState label="Загружаем портфолио" /> : portfolio.data?.length ? <div className="achievement-grid">{portfolio.data.map(item => <AchievementCard achievement={item} key={item.id} />)}</div> : <ContentState title="Портфолио пока пусто" description="После подтверждения посещения достижение появится здесь автоматически." action={<a className="button button-primary" href="/events">Выбрать событие</a>} />}</div> : null}

    {tab === "profile" && profile.data ? <div className="profile-layout"><form className="surface panel form-grid" onSubmit={event => { event.preventDefault(); const form = new FormData(event.currentTarget); saveProfile.mutate({ full_name: String(form.get("full_name")), grade: Number(form.get("grade")), region: String(form.get("region")), bio: String(form.get("bio")) }); }}><h2 className="wide">Основные данные</h2><div className="field"><label htmlFor="profile-name">Имя</label><input id="profile-name" name="full_name" defaultValue={profile.data.full_name} /></div><div className="field"><label htmlFor="profile-grade">Класс</label><input id="profile-grade" name="grade" type="number" min="1" max="11" defaultValue={profile.data.grade} /></div><div className="field"><label htmlFor="profile-region">Регион</label><input id="profile-region" name="region" defaultValue={profile.data.region} /></div><div className="field wide"><label htmlFor="profile-bio">О себе</label><textarea id="profile-bio" name="bio" defaultValue={profile.data.bio} /></div>{saveProfile.error ? <p className="error-message wide">{saveProfile.error.message}</p> : null}<button className="button button-primary" disabled={saveProfile.isPending}>Сохранить</button></form><div className="surface panel"><h2>Интересы</h2><p className="muted">По ним мы поднимаем подходящие события в рекомендациях.</p><div className="interest-grid">{categories.data?.map(category => <button className={selected.has(category.id) ? "active" : ""} key={category.id} onClick={() => toggleInterest(category.id)} type="button">{category.name}</button>)}</div>{interests.error ? <p className="error-message">{interests.error.message}</p> : null}</div></div> : null}
  </div></section></AppShell>;
}
