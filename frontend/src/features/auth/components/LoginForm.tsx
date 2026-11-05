import { useState, type FormEvent } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../../../lib/api-client";
import { useLogin } from "../hooks";
import "./LoginForm.css";

const defaultEmail = "student@talenthub.by";

export function LoginForm() {
  const [email, setEmail] = useState(defaultEmail);
  const [password, setPassword] = useState("");
  const loginMutation = useLogin();
  const navigate = useNavigate();
  const location = useLocation();
  const requestedDestination = (location.state as { from?: string } | null)?.from;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    loginMutation.mutate(
      { email, password },
      {
        onSuccess: (user) =>
          void navigate(
            requestedDestination ?? (user.role === "student" ? "/student" : "/organization"),
            { replace: true },
          ),
      },
    );
  }

  const errorMessage =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.message
      : loginMutation.isError
        ? "Не удалось войти. Попробуйте ещё раз."
        : null;

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <div className="login-form__heading">
        <h1>Вход</h1>
        <p>Войдите, чтобы продолжить.</p>
      </div>

      <label className="field">
        <span>Электронная почта</span>
        <input
          autoComplete="email"
          inputMode="email"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          required
          type="email"
          value={email}
        />
      </label>

      <label className="field">
        <span>Пароль</span>
        <input
          autoComplete="current-password"
          minLength={8}
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>

      {errorMessage ? <p className="form-error" role="alert">{errorMessage}</p> : null}

      <button className="primary-button" disabled={loginMutation.isPending} type="submit">
        {loginMutation.isPending ? "Входим…" : "Войти"}
      </button>
    </form>
  );
}
