import "./LoadingState.css";

export function LoadingState({ label = "Загружаем данные" }: { label?: string }) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <span className="loading-state__dots" aria-hidden="true"><i /><i /><i /></span>
      <span>{label}</span>
    </div>
  );
}
