import { useNavigate } from "react-router-dom";

import { FullPageStatus } from "../components/feedback/FullPageStatus";

export function NotFoundPage() {
  const navigate = useNavigate();
  return (
    <FullPageStatus
      title="Страница не найдена"
      description="Проверьте адрес или вернитесь в личный кабинет."
      actionLabel="В кабинет"
      onAction={() => void navigate("/account")}
    />
  );
}
