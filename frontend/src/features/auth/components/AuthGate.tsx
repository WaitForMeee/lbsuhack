import type { PropsWithChildren } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { FullPageStatus } from "../../../components/feedback/FullPageStatus";
import { useCurrentUser } from "../hooks";

export function AuthGate({ children }: PropsWithChildren) {
  const location = useLocation();
  const currentUser = useCurrentUser();

  if (currentUser.isPending) {
    return <FullPageStatus title="Проверяем сессию" description="Это займёт несколько секунд." />;
  }

  if (currentUser.isError) {
    return (
      <FullPageStatus
        title="Не удалось связаться с TalentHub"
        description="Проверьте, запущен ли сервер, и повторите попытку."
        actionLabel="Повторить"
        onAction={() => void currentUser.refetch()}
      />
    );
  }

  if (!currentUser.data) {
    return <Navigate replace to="/login" state={{ from: location.pathname }} />;
  }

  return children;
}
