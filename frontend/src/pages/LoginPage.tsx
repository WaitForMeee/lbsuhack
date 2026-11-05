import { Navigate } from "react-router-dom";

import { BrandMark } from "../components/brand/BrandMark";
import { FullPageStatus } from "../components/feedback/FullPageStatus";
import { LoginForm } from "../features/auth/components/LoginForm";
import { useCurrentUser } from "../features/auth/hooks";
import "./LoginPage.css";

export function LoginPage() {
  const currentUser = useCurrentUser();

  if (currentUser.isPending) {
    return <FullPageStatus title="Открываем TalentHub" description="Проверяем сохранённую сессию." />;
  }

  if (currentUser.data) {
    return <Navigate replace to={currentUser.data.role === "student" ? "/student" : "/organization"} />;
  }

  return (
    <main className="login-page">
      <header className="login-page__header">
        <BrandMark />
      </header>
      <section className="login-page__content">
        <div className="login-page__panel">
          <LoginForm />
          <p className="login-page__register">Нет аккаунта? <a href="/register">Создать</a></p>
        </div>
      </section>
    </main>
  );
}
