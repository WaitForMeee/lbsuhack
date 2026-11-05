import { BrandMark } from "../brand/BrandMark";
import "./FullPageStatus.css";

interface FullPageStatusProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function FullPageStatus({ title, description, actionLabel, onAction }: FullPageStatusProps) {
  return (
    <main className="status-page">
      <BrandMark />
      <section className="status-card">
        <span className="status-card__signal" aria-hidden="true" />
        <h1>{title}</h1>
        <p>{description}</p>
        {actionLabel && onAction ? (
          <button className="status-card__action" onClick={onAction} type="button">
            {actionLabel}
          </button>
        ) : null}
      </section>
    </main>
  );
}
