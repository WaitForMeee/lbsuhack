import type { Registration } from "../types";
import { formatDate } from "./EventCard";
import "./RegistrationCard.css";

const statusLabels = {
  pending: "На рассмотрении",
  approved: "Подтверждена",
  rejected: "Отклонена",
  cancelled: "Отменена",
  attended: "Участие подтверждено",
} as const;

const fallback = "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=900&q=80";

export function RegistrationCard({ registration, onCancel, isCancelling = false }: { registration: Registration; onCancel?: () => void; isCancelling?: boolean }) {
  const cancellable = registration.status === "pending" || registration.status === "approved";
  return <article className="registration-card surface"><a className="registration-card__image" href={"/events/" + registration.event_slug}><img src={registration.event_image_url ?? fallback} alt="" /></a><div className="registration-card__content"><div><span className={"status status--" + registration.status}>{statusLabels[registration.status]}</span><h3><a href={"/events/" + registration.event_slug}>{registration.event_title}</a></h3><p>{formatDate(registration.event_starts_at)} · {registration.organizer_name}</p></div>{cancellable && onCancel ? <button className="button button-ghost" disabled={isCancelling} onClick={onCancel} type="button">Отменить заявку</button> : null}</div></article>;
}
