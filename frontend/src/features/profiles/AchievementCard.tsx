import type { Achievement } from "./api";
import "./AchievementCard.css";

const fallback = "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=900&q=80";

export function AchievementCard({ achievement }: { achievement: Achievement }) {
  const issuedAt = new Intl.DateTimeFormat("ru-BY", { day: "numeric", month: "long", year: "numeric" }).format(new Date(achievement.issued_at));
  return <article className="achievement-card surface"><a href={"/events/" + achievement.event_slug}><img src={achievement.event_image_url ?? fallback} alt="" /></a><div className="achievement-card__body"><span className="status status--attended">Подтверждено</span><h3><a href={"/events/" + achievement.event_slug}>{achievement.title}</a></h3><p>{achievement.description}</p><small>{achievement.organizer_name} · {issuedAt}</small></div></article>;
}
